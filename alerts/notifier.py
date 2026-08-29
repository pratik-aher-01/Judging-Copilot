"""
notifier.py — Alert dispatcher for flagged judging verdicts.

Responsibilities:
  - Inspect a Verdict object after scoring and duplicate-checking
  - Send an alert (e.g. console log, webhook, email) if duplicate_flag is True
    or if score falls below a configurable threshold

Contract (backend-pipeline skill):
  Input : verdict: Verdict  (dataclass from agent/orchestrator.py)
  Output: None              (fire-and-forget side effect)
  Raises: RuntimeError if alert dispatch fails critically (log-and-continue acceptable)

Rules:
  - Reads the Verdict — never modifies it
  - Does not write to Firestore
  - Alert channel (console / webhook / email) is configured via .env — not hardcoded
"""

LOW_SCORE_THRESHOLD = 40.0  # scores below this trigger a low-score alert


def maybe_alert(verdict) -> None:
    """
    Send an alert if the verdict meets flagging criteria.

    Criteria:
      - verdict.duplicate_flag is True  → "Duplicate submission detected" alert
      - verdict.score < LOW_SCORE_THRESHOLD → "Low score" alert

    Args:
        verdict: A Verdict dataclass instance from agent/orchestrator.py.

    Returns:
        None

    Raises:
        RuntimeError: If a critical alert channel fails (e.g. webhook 5xx).
                      Non-critical failures (e.g. optional email) are logged only.
    """
    # TODO:
    #   1. Check verdict.duplicate_flag → dispatch duplicate alert
    #   2. Check verdict.score < LOW_SCORE_THRESHOLD → dispatch low-score alert
    #   3. Alert channel: start with print/logging, replace with webhook later
    raise NotImplementedError("maybe_alert is not yet implemented")
