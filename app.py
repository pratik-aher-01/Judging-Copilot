"""
app.py — FastAPI entrypoint for Judging Copilot.

Responsibilities:
  - Expose HTTP endpoints for submitting a repo URL and retrieving verdicts
  - Delegate ALL business logic to agent/orchestrator.py — no pipeline logic here
  - Load environment variables via python-dotenv on startup

API surface (initial):
  POST /judge   { "repo_url": "https://github.com/..." }
                → Verdict JSON or error detail

Rules (AGENT.md conventions):
  - Do NOT call pipeline steps (clone, score, duplicate_check) directly
  - Do NOT write to Firestore directly
  - Do NOT call Gemini directly
"""

from dotenv import load_dotenv

load_dotenv()  # must happen before any env reads

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="Judging Copilot",
    description="Automated hackathon submission scoring and duplicate detection.",
    version="0.1.0",
)


class JudgeRequest(BaseModel):
    repo_url: HttpUrl


class JudgeResponse(BaseModel):
    repo_url: str
    score: float
    rubric_breakdown: dict
    duplicate_flag: bool
    similarity_score: float
    timestamp: str
    error: str | None = None


@app.post("/judge", response_model=JudgeResponse, summary="Score a submission")
async def judge(request: JudgeRequest) -> JudgeResponse:
    """
    Accept a public GitHub repo URL and run the full judging pipeline.

    Returns a Verdict containing the score, rubric breakdown, and duplicate flag.
    """
    # TODO:
    #   from agent.orchestrator import run_pipeline
    #   verdict = run_pipeline(str(request.repo_url))
    #   return JudgeResponse(**dataclasses.asdict(verdict))
    raise HTTPException(status_code=501, detail="Judging pipeline not yet implemented")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
