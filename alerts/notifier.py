"""
notifier.py — Alert dispatcher for flagged judging verdicts.

Contract (backend-pipeline skill):
  Input : verdict: Verdict  (dataclass from agent/orchestrator.py)
  Output: None              (fire-and-forget side effect)
  Raises: Never — all failures are caught and logged; alerting is best-effort

Rules:
  - Reads the Verdict — never modifies it
  - Does not write to Firestore
  - Current channel: structured log messages (easily upgraded to Slack/webhook)
  - Both trigger conditions can fire simultaneously (duplicate AND low score)
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds — single source of truth
# ---------------------------------------------------------------------------

# Scores below this trigger a low-score alert.
# Scorer uses a 0–100 scale (4 × 0–25 criteria), so 40 = below average on all.
LOW_SCORE_THRESHOLD = 40.0

# Separator used in alert messages for readability in logs
_SEP = "=" * 60


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def maybe_alert(verdict) -> None:
    """
    Emit structured alert log messages if the verdict meets flagging criteria.

    Trigger conditions (both may fire for the same verdict):
      1. verdict.duplicate_flag is True  → duplicate submission alert
      2. verdict.score < LOW_SCORE_THRESHOLD → low score alert

    If neither condition is met, logs a brief clean-pass message at DEBUG level.

    Args:
        verdict: A Verdict dataclass instance from agent/orchestrator.py.

    Returns:
        None — always. Exceptions are caught and logged; never re-raised.
    """
    try:
        _dispatch_alerts(verdict)
    except Exception as exc:  # pragma: no cover
        # Alerting must never crash the pipeline — log and continue
        logger.error(
            "ALERT DISPATCH FAILED (non-critical, verdict still returned): %s",
            exc,
        )


def _dispatch_alerts(verdict) -> None:
    """
    Internal alert logic — separated so maybe_alert can safely wrap it.
    """
    reasons: list[str] = []

    if verdict.duplicate_flag:
        reasons.append(
            f"DUPLICATE SUBMISSION — similarity score: {verdict.similarity_score:.4f} "
            f"(threshold: 0.85)"
        )

    if verdict.score < LOW_SCORE_THRESHOLD:
        reasons.append(
            f"LOW SCORE — {verdict.score:.1f}/100 "
            f"(threshold: {LOW_SCORE_THRESHOLD:.0f})"
        )

    if not reasons:
        logger.debug(
            "No alert triggered for %s (score=%.1f, duplicate=%s)",
            verdict.repo_url, verdict.score, verdict.duplicate_flag,
        )
        return

    # Build a clearly formatted alert block
    reason_lines = "\n  • ".join(reasons)
    rubric = verdict.rubric_breakdown or {}

    breakdown_lines = "\n".join(
        f"    {k}: {v}"
        for k, v in rubric.items()
        if k != "reasoning"
    )
    reasoning = rubric.get("reasoning", "")

    alert_message = (
        f"\n{_SEP}\n"
        f"[ALERT] JUDGING ALERT\n"
        f"{_SEP}\n"
        f"  Repo       : {verdict.repo_url}\n"
        f"  Score      : {verdict.score:.1f} / 100\n"
        f"  Duplicate  : {verdict.duplicate_flag} "
        f"(similarity={verdict.similarity_score:.4f})\n"
        f"  Timestamp  : {verdict.timestamp}\n"
        f"\n"
        f"  Reason(s)  :\n"
        f"  • {reason_lines}\n"
    )

    if breakdown_lines:
        alert_message += f"\n  Rubric breakdown:\n{breakdown_lines}\n"

    if reasoning:
        alert_message += f"\n  Reasoning  : {reasoning}\n"

    alert_message += f"{_SEP}"

    # Log at WARNING so it surfaces in any default logging configuration
    logger.warning(alert_message)
