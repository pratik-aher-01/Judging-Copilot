"""
duplicate_check.py — Pipeline step 3: Detect duplicate/copied submissions.

Responsibilities:
  - Compare a submission's repo_url against the fixed set in data/past_submissions/
  - Return a (duplicate_flag: bool, similarity_score: float) tuple

Contract (backend-pipeline skill):
  Input : repo_url: str
  Output: tuple[bool, float]  — (is_duplicate, similarity_score 0.0–1.0)
  Raises: RuntimeError if comparison set cannot be read

Rules:
  - Never modify data/past_submissions/ — it is a fixed reference set (AGENT.md deny rule)
  - Do NOT call Gemini here — similarity is computed locally (e.g. file hash / TF-IDF)
  - Do NOT write to Firestore — orchestrator does that
"""

from pathlib import Path

PAST_SUBMISSIONS_PATH = Path(__file__).parent.parent / "data" / "past_submissions"
SIMILARITY_THRESHOLD = 0.85  # flag as duplicate if similarity exceeds this value


def check(repo_url: str) -> tuple[bool, float]:
    """
    Check whether a submission is a duplicate of a known past submission.

    Compares the contents of the cloned repo against the fixed reference set
    in data/past_submissions/ using a local similarity metric (no Gemini call).

    Args:
        repo_url: Public GitHub URL of the submission being judged.

    Returns:
        A tuple of:
          - duplicate_flag (bool): True if similarity_score >= SIMILARITY_THRESHOLD.
          - similarity_score (float): Highest similarity found, 0.0–1.0.

    Raises:
        RuntimeError: If the past_submissions directory cannot be read.
    """
    # TODO:
    #   1. Read files from PAST_SUBMISSIONS_PATH
    #   2. Compute similarity between submission and each past entry
    #      (e.g. file-hash exact match, then TF-IDF cosine on source text)
    #   3. Return (similarity >= SIMILARITY_THRESHOLD, max_similarity)
    raise NotImplementedError("check is not yet implemented")
