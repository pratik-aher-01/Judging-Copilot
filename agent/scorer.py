"""
scorer.py — Pipeline step 2: Score a cloned repository with Gemini.

This is the ONLY module in the project that makes Gemini API calls.
All other modules must route through here — no ad-hoc genai calls elsewhere.

Contract (backend-pipeline skill):
  Input : repo_url: str, local_path: str
  Output: Verdict (from agent.orchestrator)
  Raises: RuntimeError — never returns a partial/fake Verdict on failure

Rules:
  - Always use response_schema + response_mime_type="application/json"
  - Never parse free-text output; always use response.parsed
  - Never hardcode the rubric — always read from rubric_prompt.txt
  - GEMINI_API_KEY comes from environment — never hardcoded
"""

import os
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RUBRIC_PROMPT_PATH = Path(__file__).parent / "prompts" / "rubric_prompt.txt"

# Primary Gemini model — required by the hackathon (Gemini 3.5+ constraint).
GEMINI_MODEL = "gemini-3.5-flash"

# Fallback model used when the primary is unavailable (503/429).
GEMINI_FALLBACK_MODEL = "gemini-2.0-flash"

# Retry settings for transient API errors (503 / 429 / ResourceExhausted)
MAX_RETRIES = 3          # attempts per model before giving up / falling back
RETRY_BASE_DELAY = 2.0  # seconds — doubles on each retry (2 → 4 → 8)

# Directories that add noise / blow up token counts — skip them entirely
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "build", "dist", ".next", ".nuxt", "out", "target", ".idea",
    ".vscode", "coverage", ".pytest_cache", ".mypy_cache",
}

# File extensions worth reading for code review
READABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".rb",
    ".cs", ".cpp", ".c", ".h", ".md", ".txt", ".yaml", ".yml", ".toml",
    ".json", ".html", ".css", ".sh", ".env.example", ".dockerfile",
    "Dockerfile", "Makefile",
}

# Hard cap on characters fed into the prompt (avoids exceeding context limits)
MAX_REPO_CHARS = 80_000

# Per-file character cap — prevents one giant file from crowding everything out
MAX_FILE_CHARS = 8_000


# ---------------------------------------------------------------------------
# Pydantic schema for Gemini structured output
# ---------------------------------------------------------------------------

class RubricBreakdown(BaseModel):
    code_quality: int = Field(
        description="Code quality score 0–25: readability, structure, error handling."
    )
    functionality_completeness: int = Field(
        description="Functionality & completeness score 0–25: works end-to-end, tested."
    )
    use_of_required_technology: int = Field(
        description="Use of Gemini/ADK/GCP score 0–25: meaningful, core integration."
    )
    documentation: int = Field(
        description="Documentation score 0–25: README, setup instructions, docstrings."
    )


class GeminiScoreResponse(BaseModel):
    score: int = Field(description="Overall score 0–100; must equal sum of rubric_breakdown values.")
    rubric_breakdown: RubricBreakdown
    reasoning: str = Field(
        description="2–4 sentence overall assessment explaining the scores."
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_rubric_prompt() -> str:
    """Read and return the rubric prompt template from disk."""
    try:
        return RUBRIC_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Cannot read rubric prompt at {RUBRIC_PROMPT_PATH}: {exc}"
        ) from exc


def collect_repo_contents(local_path: str) -> str:
    """
    Walk local_path and assemble a text snapshot of the repository.

    Priority order for inclusion:
      1. README (always first — most signal-dense)
      2. Python/JS/TS source files
      3. Config files (yaml, toml, Dockerfile, etc.)

    Skips SKIP_DIRS, binary-looking files, and truncates to MAX_REPO_CHARS total.

    Args:
        local_path: Absolute path to the cloned repository root.

    Returns:
        A single string of concatenated file contents with headers.

    Raises:
        RuntimeError: If local_path does not exist or is not a directory.
    """
    root = Path(local_path)
    if not root.is_dir():
        raise RuntimeError(f"Repo path does not exist or is not a directory: {local_path}")

    sections: list[str] = []
    total_chars = 0

    # Gather all candidate files, README first
    all_files: list[Path] = []
    readme_files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip any file inside a blacklisted directory
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        name_lower = path.name.lower()
        if name_lower.startswith("readme"):
            readme_files.append(path)
        elif path.suffix in READABLE_EXTENSIONS or path.name in READABLE_EXTENSIONS:
            all_files.append(path)

    # README first, then the rest (sorted for determinism)
    ordered = readme_files + sorted(all_files, key=lambda p: p.relative_to(root))

    for file_path in ordered:
        if total_chars >= MAX_REPO_CHARS:
            sections.append("\n[... additional files omitted: token limit reached ...]\n")
            break

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.debug("Skipping unreadable file: %s", file_path)
            continue

        if not content.strip():
            continue  # skip empty files

        # Truncate large individual files
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + f"\n[... {file_path.name} truncated at {MAX_FILE_CHARS} chars ...]"

        rel_path = file_path.relative_to(root)
        header = f"\n\n{'='*60}\nFILE: {rel_path}\n{'='*60}\n"
        section = header + content
        sections.append(section)
        total_chars += len(section)

    if not sections:
        return "(repository appears empty or contains no readable source files)"

    return "".join(sections)


def _build_gemini_client() -> genai.Client:
    """
    Instantiate the google-genai client from GEMINI_API_KEY env var.

    Raises:
        RuntimeError: If GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Copy .env.example to .env and fill in your key."
        )
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def score_repo(repo_url: str, local_path: str):
    """
    Score a cloned repository against the judging rubric using Gemini.

    This is the sole Gemini call-site in the entire project.

    Steps:
      1. Collect readable source files from local_path into a text snapshot
      2. Load rubric_prompt.txt and inject the snapshot into {{REPO_CONTENTS}}
      3. Call Gemini with response_schema=GeminiScoreResponse (structured JSON)
      4. Validate the parsed response and build a Verdict

    Args:
        repo_url:   Public GitHub URL of the submission (used to populate Verdict).
        local_path: Absolute path to the cloned repository root on disk.

    Returns:
        A fully populated Verdict dataclass instance.
        duplicate_flag and similarity_score are left as defaults (False / 0.0)
        because duplicate_check.py owns those fields.

    Raises:
        RuntimeError: If any of the following occur:
          - GEMINI_API_KEY is missing
          - local_path is not a valid directory
          - rubric_prompt.txt cannot be read
          - Gemini API call fails (network, quota, etc.)
          - Parsed response is missing or structurally invalid
          - Rubric breakdown scores don't sum to reported total (sanity check)
    """
    # Import here to avoid circular import (orchestrator imports scorer)
    from agent.orchestrator import Verdict

    # Step 1 — collect repo contents
    logger.info("Collecting repository contents from: %s", local_path)
    repo_contents = collect_repo_contents(local_path)

    # Step 2 — build prompt
    rubric_template = _load_rubric_prompt()
    prompt = rubric_template.replace("{{REPO_CONTENTS}}", repo_contents)

    # Step 3 — call Gemini with retry + fallback
    client = _build_gemini_client()

    def _is_transient(exc: Exception) -> bool:
        """Return True for 503 / 429 errors that are worth retrying."""
        msg = str(exc).lower()
        return any(k in msg for k in ("503", "429", "unavailable", "resource_exhausted", "quota"))

    def _call_model(model_name: str) -> object:
        """One Gemini generate_content call — raises on any error."""
        return client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiScoreResponse,
                # Gemini 3.5 replaces temperature/top_p/top_k with thinking_level.
                # 'medium' is appropriate for a structured code-review scoring task.
                thinking_config=types.ThinkingConfig(thinking_level="medium"),
                # Explicitly disable Automatic Function Calling — we have no tools
                # registered. Without this, the SDK emits an advisory warning on
                # every models.generate_content() call.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

    response = None
    last_exc: Exception | None = None

    for model_name in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL):
        logger.info("Calling Gemini (%s) for repo: %s", model_name, repo_url)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = _call_model(model_name)
                last_exc = None
                break  # success
            except Exception as exc:
                last_exc = exc
                if _is_transient(exc) and attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini %s transient error (attempt %d/%d), retrying in %.0fs: %s",
                        model_name, attempt, MAX_RETRIES, delay, exc,
                    )
                    time.sleep(delay)
                else:
                    # Hard error or last attempt — stop retrying this model
                    logger.warning(
                        "Gemini %s failed after %d attempt(s): %s",
                        model_name, attempt, exc,
                    )
                    break
        if response is not None:
            break  # don't try fallback if primary succeeded
        if model_name == GEMINI_MODEL and last_exc is not None and _is_transient(last_exc):
            logger.warning(
                "Primary model %s unavailable, falling back to %s",
                GEMINI_MODEL, GEMINI_FALLBACK_MODEL,
            )

    if response is None:
        raise RuntimeError(
            f"Gemini API call failed for {repo_url}: {last_exc}"
        ) from last_exc

    # Step 4 — validate parsed response
    parsed: GeminiScoreResponse | None = response.parsed
    if parsed is None:
        raw_text = getattr(response, "text", "(no text in response)")
        raise RuntimeError(
            f"Gemini returned no structured output for {repo_url}. "
            f"Raw response text: {raw_text[:500]}"
        )

    # Sanity-check: breakdown scores must sum to the reported total
    breakdown = parsed.rubric_breakdown
    computed_sum = (
        breakdown.code_quality
        + breakdown.functionality_completeness
        + breakdown.use_of_required_technology
        + breakdown.documentation
    )
    if computed_sum != parsed.score:
        logger.warning(
            "Score mismatch for %s: reported=%d, breakdown_sum=%d. "
            "Using breakdown sum as authoritative.",
            repo_url, parsed.score, computed_sum,
        )
        # Trust the breakdown over the headline score
        authoritative_score = computed_sum
    else:
        authoritative_score = parsed.score

    # Clamp to valid range just in case
    authoritative_score = max(0, min(100, authoritative_score))

    rubric_breakdown_dict = {
        "code_quality": breakdown.code_quality,
        "functionality_completeness": breakdown.functionality_completeness,
        "use_of_required_technology": breakdown.use_of_required_technology,
        "documentation": breakdown.documentation,
        "reasoning": parsed.reasoning,
    }

    logger.info(
        "Scored %s → %d/100 (code=%d, func=%d, tech=%d, docs=%d)",
        repo_url,
        authoritative_score,
        breakdown.code_quality,
        breakdown.functionality_completeness,
        breakdown.use_of_required_technology,
        breakdown.documentation,
    )

    return Verdict(
        repo_url=repo_url,
        score=float(authoritative_score),
        rubric_breakdown=rubric_breakdown_dict,
        duplicate_flag=False,       # duplicate_check.py owns this
        similarity_score=0.0,       # duplicate_check.py owns this
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
