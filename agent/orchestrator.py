"""
orchestrator.py — Pipeline sequencer for the Judging Copilot.

Responsibilities:
  - Accept a repo_url from app.py
  - Call each pipeline step in order: clone → score → duplicate_check
  - Collect results into a Verdict object
  - Hand the Verdict to storage/firestore_client.py for writing
  - Hand the Verdict to alerts/notifier.py for flagging
  - Catch and log all step-level exceptions; never swallow silently

Contract (backend-pipeline skill):
  Input : repo_url: str
  Output: Verdict (dataclass defined below)
  Raises: RuntimeError if a critical step fails unrecoverably

Do NOT:
  - Call Gemini directly — that lives in agent/scorer.py
  - Write to Firestore directly — that lives in storage/firestore_client.py
  - Be called from anything other than app.py
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Verdict:
    """
    Canonical output object shared by all downstream pipeline steps.

    Fields mirror the Verdict shape defined in the backend-pipeline skill:
      repo_url, score, rubric_breakdown, duplicate_flag, similarity_score, timestamp
    """
    repo_url: str
    score: float = 0.0
    rubric_breakdown: dict = field(default_factory=dict)
    duplicate_flag: bool = False
    similarity_score: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error: Optional[str] = None  # set if a step raised but pipeline continued


def run_pipeline(repo_url: str) -> Verdict:
    """
    Execute the full judging pipeline for a single submission.

    Steps (in order):
      1. clone_tool.clone_repo(repo_url)       → local_path: str
      2. scorer.score_repo(local_path)          → score, rubric_breakdown
      3. duplicate_check.check(repo_url)        → duplicate_flag, similarity_score
      4. firestore_client.write_verdict(verdict)
      5. notifier.maybe_alert(verdict)

    Args:
        repo_url: Public GitHub URL of the submission to judge.

    Returns:
        A populated Verdict object.

    Raises:
        RuntimeError: If clone or score step fails (pipeline cannot continue).
    """
    # TODO: implement step calls
    raise NotImplementedError("run_pipeline is not yet implemented")
