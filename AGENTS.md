# Judging Copilot — Hackathon Submission Verification Agent

## Stack
Python 3.11, Google ADK, Gemini API (via AI Studio key), Firestore (Firebase Spark plan), FastAPI, Cloud Run.

## Commands
run: python app.py
test: pytest
install: pip install -r requirements.txt --break-system-packages

## Conventions
- Every Gemini call goes through agent/scorer.py — no ad-hoc model calls elsewhere.
- Firestore writes only via storage/firestore_client.py — never write directly from orchestrator.py.
- Keep secrets in .env, never hardcode API keys, never commit .env.
- Rubric prompt lives in agent/prompts/rubric_prompt.txt — edit the prompt there, not inline in code.

## Skills
- Use .agent/skills/backend-pipeline for any agent/orchestrator/scorer/firestore work.
- Use .agent/skills/passionfruit-editorial + .agent/skills/dashboard-editorial-adapter
  together for ALL frontend/UI work — load both, the adapter governs how the
  base style applies to this specific dashboard.

## Deny rules
- Never modify data/past_submissions/ (fixed comparison set for the demo).
- Never push directly to main — confirm before any git push.
