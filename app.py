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

from typing import Union
import asyncio
import dataclasses
import json
import logging
import traceback

from fastapi import FastAPI, HTTPException, Path, Query, BackgroundTasks
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

# CORS — allow all origins for local dev and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


class JobStatusResponse(BaseModel):
    """Schema for background judging job status and details."""
    job_id: str
    repo_url: str
    status: str
    stage: str
    created_at: str
    updated_at: str
    pipeline_started_at: str | None = None
    pipeline_completed_at: str | None = None
    verdict_doc_id: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _normalize_url(url: str) -> str:
    """Normalize GitHub URL by stripping whitespace, trailing slashes, and .git suffix."""
    url = url.strip()
    if url.endswith(".git"):
        url = url[:-4]
    url = url.rstrip("/")
    return url


def execute_background_judging(job_id: str, repo_url: str) -> None:
    """Background worker task executing the ADK judging pipeline."""
    from storage.firestore_client import update_job
    from agent.orchestrator import run_pipeline
    from datetime import datetime, timezone

    logger.info("Background judging started for job_id=%s, repo=%s", job_id, repo_url)
    
    started_at = datetime.now(timezone.utc).isoformat()
    update_job(
        job_id=job_id,
        status="RUNNING",
        stage="RUNNING",
        pipeline_started_at=started_at,
    )

    def on_step(step_name: str, status: str, detail: str | None) -> None:
        stage_map = {
            "clone": "INSPECTING",
            "inspect": "INSPECTING",
            "score": "EVALUATING",
            "duplicate_check": "VERIFYING",
            "firestore_write": "VERIFYING",
            "alert": "VERIFYING",
        }
        stage = stage_map.get(step_name, "RUNNING")
        try:
            update_job(job_id=job_id, status="RUNNING", stage=stage)
        except Exception as exc:
            logger.warning("Failed to update job stage for job_id=%s: %s", job_id, exc)

    try:
        verdict = run_pipeline(repo_url=repo_url, on_step=on_step)
        verdict_doc_id = verdict.doc_id
        completed_at = datetime.now(timezone.utc).isoformat()
        update_job(
            job_id=job_id,
            status="COMPLETED",
            stage="COMPLETED",
            verdict_doc_id=verdict_doc_id,
            pipeline_completed_at=completed_at,
        )
        logger.info("Background judging completed for job_id=%s, verdict_doc_id=%s", job_id, verdict_doc_id)
    except Exception as exc:
        logger.error("Background judging failed for job_id=%s: %s", job_id, exc)
        completed_at = datetime.now(timezone.utc).isoformat()
        update_job(
            job_id=job_id,
            status="FAILED",
            stage="FAILED",
            error=str(exc),
            pipeline_completed_at=completed_at,
        )


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
    Run the full judging pipeline for a submitted repo URL synchronously.
    """
    from agent.orchestrator import run_pipeline

    logger.info("POST /judge received for: %s", request.repo_url)

    try:
        verdict = run_pipeline(request.repo_url)
    except RuntimeError as exc:
        logger.error("Pipeline failed for %s:\n%s", request.repo_url, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}") from exc
    except Exception as exc:
        logger.error("Unexpected error in pipeline for %s:\n%s", request.repo_url, traceback.format_exc())
        raise HTTPException(status_code=500, detail="An unexpected server error occurred. Check server logs.") from exc

    verdict_dict = dataclasses.asdict(verdict)
    return VerdictResponse(**verdict_dict)


@app.post(
    "/jobs",
    response_model=JobStatusResponse,
    status_code=202,
    summary="Create background judging job",
    description="Creates an asynchronous judging job for the given repo URL and returns immediately.",
)
async def create_judging_job(
    request: JudgeRequest,
    background_tasks: BackgroundTasks,
) -> JobStatusResponse:
    from storage.firestore_client import create_job, get_active_job_by_url
    from datetime import datetime, timezone

    normalized_url = _normalize_url(request.repo_url)
    logger.info("POST /jobs received for: %s (normalized: %s)", request.repo_url, normalized_url)

    try:
        # Prevent duplicate execution
        active_job = get_active_job_by_url(normalized_url)
        if active_job:
            logger.info("Active job already exists for %s: job_id=%s", normalized_url, active_job["job_id"])
            return JobStatusResponse(**active_job)

        # Create new job doc (using normalized URL)
        job_id = create_job(normalized_url)
        logger.info("Created new background job: %s", job_id)

        # Schedule execution (non-blocking background execution with persistent Firestore job state)
        background_tasks.add_task(execute_background_judging, job_id, normalized_url)
        
        # Return initial queued status
        now = datetime.now(timezone.utc).isoformat()
        return JobStatusResponse(
            job_id=job_id,
            repo_url=normalized_url,
            status="QUEUED",
            stage="QUEUED",
            created_at=now,
            updated_at=now,
        )
    except Exception as exc:
        logger.error("Failed to enqueue background job for %s:\n%s", request.repo_url, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {exc}") from exc


@app.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get background job status",
    description="Retrieve the current status, stage, and verdict document link of a background judging job.",
)
async def get_job_status(
    job_id: str = Path(..., description="The background job document ID"),
) -> JobStatusResponse:
    from storage.firestore_client import get_job
    try:
        job_data = get_job(job_id)
        return JobStatusResponse(**job_data)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("GET /jobs/%s failed:\n%s", job_id, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job: {exc}") from exc


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

@app.get("/", summary="Root endpoint", include_in_schema=False)
async def root() -> dict:
    return {"status": "ok", "service": "Judging Copilot API", "version": app.version, "docs": "/docs"}


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
