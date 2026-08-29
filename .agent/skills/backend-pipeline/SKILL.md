---
description: Use when building or editing any step in the judging pipeline (clone, score, duplicate-check, firestore write, alert). Ensures every agent step follows the same input/output contract.
---

# ADK pipeline pattern

Every pipeline step is a single-responsibility function that:
1. Takes a typed input (repo_url: str, or a Verdict object downstream)
2. Returns a typed output — never raw dicts
3. Raises on failure — orchestrator catches and logs, steps don't swallow errors

Gemini calls always request structured JSON output (response_schema), never free-text parsing.

Verdict object shape (used everywhere downstream of scoring):
{ repo_url, score, rubric_breakdown, duplicate_flag, similarity_score, timestamp }

New steps wire into orchestrator.py's sequence — never called standalone from app.py.
