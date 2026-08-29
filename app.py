"""
app.py — FastAPI entrypoint for Judging Copilot.

Responsibilities:
  - Expose HTTP endpoints for submitting a repo URL and retrieving verdicts
  - Delegate ALL business logic to agent/orchestrator.py — no pipeline logic here
  - Load environment variables via python-dotenv on startup

Rules (AGENT.md conventions):
  - Do NOT call pipeline steps (clone, score, duplicate_check) directly
  - Do NOT write to Firestore directly — only firestore_client.py does that
  - Do NOT call Gemini directly — only scorer.py does that
  - Stack traces stay server-side — clean error messages only to clients
"""

from dotenv import load_dotenv

load_dotenv()  # must happen before any module that reads env vars is imported

import asyncio
import dataclasses
import json
import logging
import traceback

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl, field_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Judging Copilot",
    description=(
        "Automated hackathon submission scoring, duplicate detection, "
        "and Firestore persistence."
    ),
    version="0.2.0",
)

# CORS — allow localhost for frontend dev on any common port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class JudgeRequest(BaseModel):
    repo_url: str

    @field_validator("repo_url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("repo_url must not be empty")
        if not v.startswith("https://github.com/"):
            raise ValueError(
                "repo_url must be a public GitHub HTTPS URL "
                "(e.g. https://github.com/owner/repo)"
            )
        return v


class VerdictResponse(BaseModel):
    """Mirrors the Verdict dataclass fields for API responses."""
    repo_url: str
    score: float
    rubric_breakdown: dict
    duplicate_flag: bool
    similarity_score: float
    timestamp: str
    error: str | None = None
    doc_id: str | None = None  # Firestore document ID, if write succeeded


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/judge",
    response_model=VerdictResponse,
    summary="Score a hackathon submission",
    description=(
        "Clones the given GitHub repo, scores it with Gemini, checks for "
        "duplicates, persists to Firestore, and returns the full Verdict."
    ),
)
async def judge(request: JudgeRequest) -> VerdictResponse:
    """
    Run the full judging pipeline for a submitted repo URL.

    - 400 if repo_url is missing or not a GitHub HTTPS URL
    - 500 if the pipeline fails (clone or scoring error) — stack trace logged
           server-side, clean message returned to client
    """
    from agent.orchestrator import run_pipeline

    logger.info("POST /judge received for: %s", request.repo_url)

    try:
        verdict = run_pipeline(request.repo_url)
    except RuntimeError as exc:
        # Known pipeline error — log full trace server-side, return clean message
        logger.error(
            "Pipeline failed for %s:\n%s",
            request.repo_url,
            traceback.format_exc(),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {exc}",
        ) from exc
    except Exception as exc:
        # Unexpected error — same treatment
        logger.error(
            "Unexpected error in pipeline for %s:\n%s",
            request.repo_url,
            traceback.format_exc(),
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred. Check server logs.",
        ) from exc

    # verdict.doc_id is now populated by orchestrator.run_pipeline after the
    # Firestore write — dataclasses.asdict captures it automatically.
    verdict_dict = dataclasses.asdict(verdict)
    return VerdictResponse(**verdict_dict)


@app.get(
    "/judge/stream",
    summary="Score a submission with Server-Sent Events progress",
    description=(
        "Streams real-time pipeline progress as SSE events, then a final "
        "pipeline_complete or pipeline_failed event. "
        "Use GET (EventSource-compatible) with ?repo_url=<url>."
    ),
)
async def judge_stream(
    repo_url: str = Query(..., description="Public GitHub HTTPS URL to judge"),
) -> StreamingResponse:
    """
    Run the full judging pipeline and stream each step as an SSE event.

    Event shape (JSON payload in each 'data:' line):
      { "type": "step", "step": str, "status": "started"|"completed"|"failed",
        "detail": str | null }

    Terminal events:
      { "type": "pipeline_complete", "verdict": <verdict dict> }
      { "type": "pipeline_failed",   "step": str, "error": str }

    Implementation notes:
      - run_pipeline() is blocking (git, Gemini, Firestore) — runs in a
        background thread via asyncio.to_thread so it never blocks the event loop.
      - The on_step callback is called from that worker thread; it uses
        loop.call_soon_threadsafe to safely schedule queue.put_nowait on the
        async event loop.
      - A sentinel value (None) is placed on the queue by the worker when it
        finishes (success or failure) to signal the generator to close.
    """
    # Validate URL before starting the pipeline
    if not repo_url.strip().startswith("https://github.com/"):
        raise HTTPException(
            status_code=400,
            detail="repo_url must be a public GitHub HTTPS URL (https://github.com/owner/repo)",
        )

    from agent.orchestrator import run_pipeline

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def on_step(step_name: str, status: str, detail: str | None) -> None:
        """Called from the worker thread — schedules queue.put_nowait on the loop."""
        event = {"type": "step", "step": step_name, "status": status, "detail": detail}
        loop.call_soon_threadsafe(queue.put_nowait, event)

    async def run_pipeline_task() -> None:
        """Worker: run blocking pipeline in a thread, put terminal event on queue."""
        try:
            verdict = await asyncio.to_thread(run_pipeline, repo_url, on_step)
            terminal = {
                "type": "pipeline_complete",
                "verdict": dataclasses.asdict(verdict),
            }
        except RuntimeError as exc:
            # Extract which step failed from the message ("Pipeline failed at step N (name): ...")
            msg = str(exc)
            step = "unknown"
            if "(clone)" in msg:
                step = "clone"
            elif "(score)" in msg:
                step = "score"
            terminal = {
                "type": "pipeline_failed",
                "step": step,
                "error": msg,
            }
            logger.error("SSE pipeline failed for %s: %s", repo_url, exc)
        except Exception as exc:
            terminal = {
                "type": "pipeline_failed",
                "step": "unknown",
                "error": str(exc),
            }
            logger.error("SSE unexpected error for %s:\n%s", repo_url, traceback.format_exc())
        finally:
            # Terminal event, then sentinel to close the generator
            loop.call_soon_threadsafe(queue.put_nowait, terminal)
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

    async def event_generator():
        """Async generator: reads from queue and yields SSE-formatted strings."""
        # Start the pipeline task concurrently
        asyncio.create_task(run_pipeline_task())

        while True:
            event = await queue.get()
            if event is None:  # sentinel — stream is done
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disables nginx buffering in Cloud Run
            "Connection": "keep-alive",
        },
    )

@app.get(
    "/verdicts",
    summary="List all verdicts",
    description="Returns all verdicts from Firestore, most recent first.",
)
async def list_verdicts_endpoint(limit: int = 100) -> list[dict]:
    """
    Return all stored verdicts, newest first.

    Query param:
        limit (int): Maximum number to return, default 100.
    """
    from storage.firestore_client import list_verdicts

    logger.info("GET /verdicts (limit=%d)", limit)
    try:
        return list_verdicts(limit=limit)
    except RuntimeError as exc:
        logger.error("GET /verdicts failed:\n%s", traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve verdicts: {exc}",
        ) from exc


@app.get(
    "/verdicts/{doc_id}",
    summary="Get a single verdict by Firestore document ID",
    description="Returns a single verdict document for the rubric breakdown view.",
)
async def get_verdict_endpoint(
    doc_id: str = Path(..., description="Firestore document ID"),
) -> dict:
    """
    Return one verdict by its Firestore document ID.

    - 404 if no verdict with that ID exists
    - 500 if Firestore query fails
    """
    from storage.firestore_client import get_verdict

    logger.info("GET /verdicts/%s", doc_id)
    try:
        return get_verdict(doc_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error(
            "GET /verdicts/%s failed:\n%s", doc_id, traceback.format_exc()
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve verdict: {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check", include_in_schema=False)
async def health() -> dict:
    return {"status": "ok", "version": app.version}


# ---------------------------------------------------------------------------
# Dev server entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
