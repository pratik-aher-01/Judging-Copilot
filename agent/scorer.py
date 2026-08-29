"""
scorer.py — Pipeline step 2: Score a cloned repository with Gemini.

Responsibilities:
  - Load the rubric prompt from agent/prompts/rubric_prompt.txt
  - Build a Gemini request using response_schema for structured JSON output
  - Return a (score: float, rubric_breakdown: dict) tuple

Contract (backend-pipeline skill):
  Input : local_path: str  (path returned by clone_tool)
  Output: tuple[float, dict]  — (score 0-100, rubric breakdown keyed by criterion)
  Raises: RuntimeError if Gemini call fails or response fails schema validation

Rules:
  - ALL Gemini calls in the project live here — no ad-hoc model calls elsewhere
  - Always use response_schema — never parse free-text Gemini output
  - Never hardcode the rubric inline; always read from rubric_prompt.txt
"""

import os
from pathlib import Path

RUBRIC_PROMPT_PATH = Path(__file__).parent / "prompts" / "rubric_prompt.txt"


def _load_rubric_prompt() -> str:
    """Read and return the rubric prompt from disk."""
    return RUBRIC_PROMPT_PATH.read_text(encoding="utf-8")


def score_repo(local_path: str) -> tuple[float, dict]:
    """
    Score a cloned repository against the judging rubric using Gemini.

    Reads relevant source files from local_path, assembles a prompt using
    the rubric template, calls the Gemini API with a structured response_schema,
    and returns a validated score and breakdown.

    Args:
        local_path: Absolute path to the cloned repository root.

    Returns:
        A tuple of:
          - score (float): Overall score 0–100.
          - rubric_breakdown (dict): Per-criterion scores and rationale.

    Raises:
        RuntimeError: If the Gemini API call fails or the response is invalid.
    """
    # TODO:
    #   1. Walk local_path and collect key file contents (README, main source files)
    #   2. Load rubric prompt via _load_rubric_prompt()
    #   3. Build Gemini request with response_schema defining score + breakdown fields
    #   4. Call Gemini via google-genai SDK (use GEMINI_API_KEY from env)
    #   5. Validate and return (score, rubric_breakdown)
    raise NotImplementedError("score_repo is not yet implemented")
