"""
duplicate_check.py — Pipeline step 3: Detect duplicate/copied submissions.

Contract (backend-pipeline skill):
  Input : repo_path: str  (absolute path to the cloned submission repo)
  Output: tuple[bool, float]  — (duplicate_flag, similarity_score 0.0–1.0)
  Raises: RuntimeError if past_submissions/ is empty or embedding fails

Rules:
  - Content collection reuses scorer.collect_repo_contents — no duplication
  - Embeddings for past_submissions/ are cached to a .json file on first run;
    only regenerated if the set of past-submission directories changes
  - Embedding model: gemini-embedding-001 (verified stable, Aug 2026)
  - Cosine similarity computation is done locally — no extra Gemini call
  - GEMINI_API_KEY from environment; never hardcoded
  - Does NOT write to Firestore — orchestrator handles that
  - Never modifies data/past_submissions/ contents (AGENT.md deny rule)
"""

import json
import logging
import math
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAST_SUBMISSIONS_DIR = Path(__file__).parent.parent / "data" / "past_submissions"
EMBEDDING_CACHE_PATH = PAST_SUBMISSIONS_DIR / ".embedding_cache.json"

# Verified stable embedding model name (google-genai SDK, Aug 2026).
# gemini-embedding-001 supersedes the legacy text-embedding-004/005 models.
EMBEDDING_MODEL = "gemini-embedding-001"

# Flag as duplicate if cosine similarity exceeds this threshold
SIMILARITY_THRESHOLD = 0.85

# Truncate embedding input — embedding models have context limits too
MAX_EMBED_CHARS = 30_000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_embed_client():
    """
    Instantiate the google-genai client from GEMINI_API_KEY env var.

    Raises:
        RuntimeError: If GEMINI_API_KEY is not set.
    """
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. "
            "Copy .env.example to .env and fill in your key."
        )
    return genai.Client(api_key=api_key)


def _get_embedding(client, text: str) -> list[float]:
    """
    Generate an embedding vector for the given text using EMBEDDING_MODEL.

    Truncates text to MAX_EMBED_CHARS before calling the API.

    Args:
        client: google.genai.Client instance.
        text:   Text to embed.

    Returns:
        List of floats representing the embedding vector.

    Raises:
        RuntimeError: If the API call fails or returns no embedding.
    """
    truncated = text[:MAX_EMBED_CHARS]
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=truncated,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Embedding API call failed ({EMBEDDING_MODEL}): {exc}"
        ) from exc

    # response.embeddings is a list of ContentEmbedding objects
    embeddings = getattr(response, "embeddings", None)
    if not embeddings:
        raise RuntimeError(
            f"Embedding model returned no embeddings for input text "
            f"(model={EMBEDDING_MODEL}, input_len={len(truncated)})"
        )
    return embeddings[0].values


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """
    Compute cosine similarity between two equal-length vectors.

    Returns a float in [-1.0, 1.0]. Returns 0.0 if either vector is zero.
    """
    if len(a) != len(b):
        raise ValueError(
            f"Vector length mismatch: {len(a)} vs {len(b)}"
        )
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def _list_past_submission_dirs() -> list[Path]:
    """
    Return a sorted list of subdirectory Paths inside PAST_SUBMISSIONS_DIR.

    Each subdirectory is expected to be a cloned past submission repo.

    Raises:
        RuntimeError: If the directory doesn't exist or is empty.
    """
    if not PAST_SUBMISSIONS_DIR.is_dir():
        raise RuntimeError(
            f"past_submissions directory does not exist: {PAST_SUBMISSIONS_DIR}"
        )
    dirs = sorted(
        p for p in PAST_SUBMISSIONS_DIR.iterdir()
        if p.is_dir()
    )
    if not dirs:
        raise RuntimeError(
            f"data/past_submissions/ is empty — no reference repos to compare against. "
            f"Add at least one past submission directory to {PAST_SUBMISSIONS_DIR}"
        )
    return dirs


def _load_cache() -> dict:
    """Load the embedding cache from disk. Returns empty dict if not present."""
    if EMBEDDING_CACHE_PATH.exists():
        try:
            return json.loads(EMBEDDING_CACHE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Embedding cache unreadable, rebuilding: %s", exc)
    return {}


def _save_cache(cache: dict) -> None:
    """Persist the embedding cache to disk."""
    try:
        EMBEDDING_CACHE_PATH.write_text(
            json.dumps(cache, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        logger.warning("Could not write embedding cache: %s", exc)


def _get_past_embeddings(client) -> dict[str, list[float]]:
    """
    Return a dict mapping past-submission dir name → embedding vector.

    Strategy:
      - Load cache from .embedding_cache.json
      - Determine which dirs are new (not in cache) or missing from cache
      - Embed only the new/missing ones; skip the rest (cache hit)
      - Save updated cache before returning

    Args:
        client: google.genai.Client instance.

    Returns:
        Dict of {dir_name: embedding_vector} for all past submissions.

    Raises:
        RuntimeError: If past_submissions/ is empty.
    """
    from agent.scorer import collect_repo_contents

    past_dirs = _list_past_submission_dirs()
    cache = _load_cache()
    current_dir_names = {d.name for d in past_dirs}

    # Evict stale entries (dirs that no longer exist)
    stale_keys = [k for k in cache if k not in current_dir_names]
    for k in stale_keys:
        logger.debug("Evicting stale cache entry: %s", k)
        del cache[k]

    # Embed any dirs not yet in cache
    newly_embedded = 0
    for past_dir in past_dirs:
        if past_dir.name in cache:
            logger.debug("Cache hit for past submission: %s", past_dir.name)
            continue

        logger.info(
            "Generating embedding for past submission: %s", past_dir.name
        )
        try:
            contents = collect_repo_contents(str(past_dir))
            embedding = _get_embedding(client, contents)
            cache[past_dir.name] = embedding
            newly_embedded += 1
        except Exception as exc:
            # A broken past submission shouldn't block the whole check —
            # log and skip. It simply won't participate in comparison.
            logger.warning(
                "Could not embed past submission %s (skipping): %s",
                past_dir.name, exc,
            )

    if newly_embedded > 0:
        _save_cache(cache)
        logger.info("Embedding cache updated (%d new entries)", newly_embedded)

    return cache


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def check_duplicate(repo_path: str) -> tuple[bool, float]:
    """
    Check whether a cloned submission is a duplicate of a known past submission.

    Steps:
      1. Collect repo contents via scorer.collect_repo_contents (shared logic)
      2. Generate an embedding for the submission using gemini-embedding-001
      3. Load/update the cached embeddings for all past submissions
      4. Compute cosine similarity against each past submission embedding
      5. Return (True, max_similarity) if any similarity >= SIMILARITY_THRESHOLD,
         else (False, max_similarity)

    Args:
        repo_path: Absolute path to the cloned submission repository root.

    Returns:
        A tuple of:
          - duplicate_flag (bool): True if max similarity >= SIMILARITY_THRESHOLD.
          - similarity_score (float): Highest cosine similarity found (0.0–1.0).

    Raises:
        RuntimeError: If past_submissions/ is empty, GEMINI_API_KEY is missing,
                      or the embedding API call fails.
    """
    from agent.scorer import collect_repo_contents

    logger.info("Running duplicate check for: %s", repo_path)

    # Step 1 + 2 — embed the submission
    client = _build_embed_client()
    contents = collect_repo_contents(repo_path)
    submission_embedding = _get_embedding(client, contents)

    # Step 3 — load/build past-submission embeddings (cached)
    past_embeddings = _get_past_embeddings(client)

    if not past_embeddings:
        # All past submissions failed to embed — degrade gracefully
        logger.warning(
            "No valid past-submission embeddings available; "
            "duplicate check returning False with score 0.0"
        )
        return False, 0.0

    # Step 4 — compare
    max_similarity = 0.0
    most_similar = None
    for name, past_vec in past_embeddings.items():
        try:
            sim = _cosine_similarity(submission_embedding, past_vec)
        except ValueError as exc:
            logger.warning("Skipping comparison with %s: %s", name, exc)
            continue
        if sim > max_similarity:
            max_similarity = sim
            most_similar = name

    # Step 5 — threshold decision
    duplicate_flag = max_similarity >= SIMILARITY_THRESHOLD
    if duplicate_flag:
        logger.warning(
            "DUPLICATE DETECTED: similarity=%.4f against '%s' (threshold=%.2f)",
            max_similarity, most_similar, SIMILARITY_THRESHOLD,
        )
    else:
        logger.info(
            "No duplicate found: max_similarity=%.4f against '%s'",
            max_similarity, most_similar,
        )

    return duplicate_flag, round(max_similarity, 4)
