# Judging Copilot

Automated hackathon submission verification agent built with Google ADK, Gemini, and Firestore.

## What it does
- Clones a submitted GitHub repository
- Scores it against a rubric using Gemini (structured JSON output, no free-text parsing)
- Detects duplicate or plagiarised submissions against a fixed reference set
- Persists verdicts to Firestore
- Alerts organizers on flagged submissions

## Stack
Python 3.11 · Google ADK · Gemini API · Firestore (Firebase Spark) · FastAPI · Cloud Run

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt --break-system-packages

# 2. Configure secrets
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY and FIREBASE_CREDENTIALS_PATH

# 3. Run the server
python app.py
```

The API will be available at `http://localhost:8000`.

## API

### `POST /judge`
Score a submission.

**Request body:**
```json
{ "repo_url": "https://github.com/owner/repo" }
```

**Response:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "score": 82.5,
  "rubric_breakdown": { "innovation": 22, "technical_depth": 20, "completeness": 21, "impact": 19 },
  "duplicate_flag": false,
  "similarity_score": 0.12,
  "timestamp": "2026-08-29T04:00:00+00:00"
}
```

## Project structure

```
agent/
  orchestrator.py       # Pipeline sequencer — only entry point from app.py
  clone_tool.py         # Step 1: clone repo
  scorer.py             # Step 2: Gemini scoring (ALL model calls live here)
  duplicate_check.py    # Step 3: similarity against past_submissions/
  prompts/
    rubric_prompt.txt   # Edit rubric criteria here, not inline in code
storage/
  firestore_client.py   # ALL Firestore writes go through here
alerts/
  notifier.py           # Alert dispatcher for flagged verdicts
data/
  past_submissions/     # Fixed reference set — never modify
app.py                  # FastAPI entrypoint
```

## Development

```bash
# Run tests
pytest

# The server auto-reloads in dev mode (uvicorn reload=True)
python app.py
```
