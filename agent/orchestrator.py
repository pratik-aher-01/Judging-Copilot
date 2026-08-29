"""
orchestrator.py — Pipeline sequencer for the Judging Copilot.

ADK 2.8.0 integration (verified working pattern):
  Five pipeline steps run as ADK FunctionNodes inside a Workflow.

  Data threading pattern (empirically verified before implementation):
    - First node  (clone):  parameter_binding='state'      — reads repo_url
                                                              from session state
    - Nodes 2–5:            parameter_binding='node_input' — each receives the
                                                              previous node's
                                                              accumulated dict output

  Schema override: each FunctionNode's input_schema and output_schema are set
  to {'additionalProperties': True, 'type': 'object'} BEFORE the Workflow is
  constructed to bypass the title-mismatch in ADK's graph schema validator
  (which compares auto-generated "XParams" titles against return type titles).

Rules (AGENT.md conventions):
  - Do NOT call Gemini directly — that lives in agent/scorer.py
  - Do NOT write to Firestore directly — that lives in storage/firestore_client.py
  - Do NOT be called from anything other than app.py
"""

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools.tool_context import ToolContext
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

# Open JSON Schema used on every FunctionNode to bypass ADK's title-match
# validation while still allowing any dict to flow between nodes.
_OPEN_SCHEMA = {"additionalProperties": True, "type": "object"}


# ---------------------------------------------------------------------------
# on_step callback type  (unchanged from pre-ADK version)
# ---------------------------------------------------------------------------

StepCallback = Callable[[str, str, Optional[str]], None]


def _noop(*args, **kwargs) -> None:  # noqa: ANN001
    """Default no-op so callers without on_step work unchanged."""


# ---------------------------------------------------------------------------
# Verdict — canonical output object shared across all pipeline steps
# ---------------------------------------------------------------------------

@dataclass
class Verdict:
    """
    Canonical output object shared by all downstream pipeline steps.

    Fields mirror the Verdict shape from the backend-pipeline skill:
      repo_url, score, rubric_breakdown, duplicate_flag, similarity_score, timestamp

    error  is set only if a non-critical step fails after scoring is complete.
    doc_id is the Firestore document ID set after a successful write.
    """
    repo_url: str
    score: float = 0.0
    rubric_breakdown: dict = field(default_factory=dict)
    duplicate_flag: bool = False
    similarity_score: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error: Optional[str] = None
    doc_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Tool wrappers for LlmAgent
# ---------------------------------------------------------------------------

def tool_clone_repo(repo_url: str, tool_context: ToolContext) -> str:
    """Clones a public GitHub repository to a local temporary directory.

    Args:
        repo_url: The public GitHub URL of the repository to clone.

    Returns:
        The absolute local path where the repository has been cloned.
    """
    from agent.clone_tool import clone_repo
    cb = tool_context.state.get("on_step") or _noop
    cb("clone", "started", f"Cloning {repo_url}")
    try:
        local_path = clone_repo(repo_url)
        cb("clone", "completed", f"Cloned to {local_path}")
        # Save local_path in the state so subsequent tools can use it
        tool_context.state["local_path"] = local_path
        return local_path
    except Exception as exc:
        cb("clone", "failed", str(exc))
        raise RuntimeError(f"Pipeline failed at step 1 (clone): {exc}") from exc


def tool_score_repo(repo_url: str, local_path: str, tool_context: ToolContext) -> dict:
    """Evaluates and scores a cloned repository against the judging rubric using Gemini.

    Args:
        repo_url: The public GitHub URL of the repository.
        local_path: The absolute local path where the repository is cloned.

    Returns:
        A dictionary containing:
          - score: The total rubric score (0.0 to 100.0)
          - rubric_breakdown: A dictionary containing details of scores and text reasoning
          - timestamp: The evaluation ISO timestamp
    """
    from agent.scorer import score_repo
    cb = tool_context.state.get("on_step") or _noop
    cb("score", "started", "Scoring repository with Gemini ...")
    try:
        verdict = score_repo(repo_url=repo_url, local_path=local_path)
        cb("score", "completed", f"Score: {verdict.score:.1f}/100")
        
        # Save results to context state
        tool_context.state["score"] = verdict.score
        tool_context.state["rubric_breakdown"] = verdict.rubric_breakdown
        tool_context.state["timestamp"] = verdict.timestamp
        return {
            "score": verdict.score,
            "rubric_breakdown": verdict.rubric_breakdown,
            "timestamp": verdict.timestamp,
        }
    except Exception as exc:
        _cleanup_clone(local_path)
        cb("score", "failed", str(exc))
        raise RuntimeError(f"Pipeline failed at step 2 (score): {exc}") from exc


def tool_check_duplicate(local_path: str, tool_context: ToolContext) -> dict:
    """Checks the similarity of the cloned repository against past submissions.

    Args:
        local_path: The absolute local path where the repository is cloned.

    Returns:
        A dictionary containing:
          - duplicate_flag: True if a potential duplicate is detected, else False
          - similarity_score: The highest cosine similarity score (0.0 to 1.0)
    """
    from agent.duplicate_check import check_duplicate
    cb = tool_context.state.get("on_step") or _noop
    cb("duplicate_check", "started", "Checking for duplicate submissions ...")
    try:
        dup_flag, sim_score = check_duplicate(repo_path=local_path)
        detail = (
            f"Duplicate detected (similarity={sim_score:.4f})"
            if dup_flag
            else f"No duplicate (max_similarity={sim_score:.4f})"
        )
        cb("duplicate_check", "completed", detail)
        tool_context.state["duplicate_flag"] = dup_flag
        tool_context.state["similarity_score"] = sim_score
        return {
            "duplicate_flag": dup_flag,
            "similarity_score": sim_score,
        }
    except Exception as exc:
        cb("duplicate_check", "failed", f"Skipped: {exc}")
        logger.warning("[dup_check] soft-fail: %s", exc)
        tool_context.state["duplicate_flag"] = False
        tool_context.state["similarity_score"] = 0.0
        return {
            "duplicate_flag": False,
            "similarity_score": 0.0,
            "error": str(exc),
        }
    finally:
        _cleanup_clone(local_path)


def tool_firestore_write(
    repo_url: str,
    score: float,
    rubric_breakdown: dict,
    duplicate_flag: bool,
    similarity_score: float,
    timestamp: str,
    tool_context: ToolContext,
) -> str:
    """Persists the judging verdict to Firestore.

    Args:
        repo_url: The repository URL.
        score: The total score.
        rubric_breakdown: The score details and reasoning.
        duplicate_flag: True if duplicate warning triggered.
        similarity_score: The highest similarity score.
        timestamp: The evaluation ISO timestamp.

    Returns:
        The generated Firestore document ID.
    """
    from storage.firestore_client import write_verdict
    cb = tool_context.state.get("on_step") or _noop
    cb("firestore_write", "started", "Persisting verdict to Firestore ...")
    
    verdict_obj = Verdict(
        repo_url=repo_url,
        score=score,
        rubric_breakdown=rubric_breakdown,
        duplicate_flag=duplicate_flag,
        similarity_score=similarity_score,
        timestamp=timestamp,
    )
    try:
        new_doc_id = write_verdict(verdict_obj)
        cb("firestore_write", "completed", f"Saved as doc_id={new_doc_id}")
        tool_context.state["doc_id"] = new_doc_id
        return new_doc_id
    except Exception as exc:
        logger.error("[firestore_write] soft-fail: %s", exc)
        cb("firestore_write", "failed", str(exc))
        tool_context.state["error"] = f"Firestore write failed: {exc}"
        return ""


def tool_alert(
    repo_url: str,
    score: float,
    rubric_breakdown: dict,
    duplicate_flag: bool,
    similarity_score: float,
    timestamp: str,
    doc_id: str = "",
    error: str = "",
    tool_context: ToolContext = None,
) -> str:
    """Runs alert checks and prints notification logs if triggers are met.

    Args:
        repo_url: The repository URL.
        score: The total score.
        rubric_breakdown: The score details and reasoning.
        duplicate_flag: True if duplicate warning triggered.
        similarity_score: The highest similarity score.
        timestamp: The evaluation ISO timestamp.
        doc_id: The Firestore document ID (optional).
        error: The pipeline error status if any (optional).

    Returns:
        A confirmation message.
    """
    from alerts.notifier import maybe_alert
    cb = tool_context.state.get("on_step") or _noop
    cb("alert", "started", "Running alert check ...")
    
    verdict_obj = Verdict(
        repo_url=repo_url,
        score=score,
        rubric_breakdown=rubric_breakdown,
        duplicate_flag=duplicate_flag,
        similarity_score=similarity_score,
        timestamp=timestamp,
        doc_id=doc_id or None,
        error=error or None,
    )
    try:
        maybe_alert(verdict_obj)
        cb("alert", "completed", "Alert check done")
        return "Alert processed successfully."
    except Exception as exc:
        logger.error("[alert] soft-fail: %s", exc)
        cb("alert", "failed", str(exc))
        return f"Alert failed: {exc}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cleanup_clone(local_path: Optional[str]) -> None:
    """Remove the cloned repo from disk. Never re-raises."""
    if not local_path:
        return
    try:
        shutil.rmtree(local_path, ignore_errors=True)
        logger.debug("Cleaned up clone directory: %s", local_path)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to clean up clone directory %s: %s", local_path, exc)


# ---------------------------------------------------------------------------
# ADK Coordinator Agent definition
# ---------------------------------------------------------------------------

JUDGE_AGENT_INSTRUCTION = """
You are the Hackathon Judging Agent coordinator.
Your goal is to evaluate the submitted public GitHub repository.

You must perform the following actions in exact order:
1. Clone the repository using the `tool_clone_repo` tool. (The repository URL is provided in the session state `repo_url` or user query).
2. Evaluate and score the repository using `tool_score_repo`.
3. Check for duplicate submissions using `tool_check_duplicate`.
4. Persist the judging verdict to Firestore using `tool_firestore_write`.
5. Trigger alerts using `tool_alert`.

If any critical step (cloning or scoring) fails and raises an error, you must stop and report the failure.
Do not guess scores or duplicate status. Always call the tools to gather evidence.
"""

judge_agent = LlmAgent(
    name="judging_agent",
    model="gemini-3.5-flash",
    instruction=JUDGE_AGENT_INSTRUCTION,
    tools=[
        tool_clone_repo,
        tool_score_repo,
        tool_check_duplicate,
        tool_firestore_write,
        tool_alert,
    ],
)


# ---------------------------------------------------------------------------
# Public interface — signature identical to the pre-ADK version
# ---------------------------------------------------------------------------

def run_pipeline(
    repo_url: str,
    on_step: Optional[StepCallback] = None,
) -> Verdict:
    """
    Execute the judging pipeline via an autonomous ADK LlmAgent.

    The agent coordinates the pipeline by invoking clone, score, duplicate check,
    firestore write, and alert tools dynamically.

    Args:
        repo_url: Public GitHub HTTPS URL of the submission to judge.
        on_step:  Optional callback (step_name, status, detail) fired at each stage.

    Returns:
        A fully populated Verdict dataclass.

    Raises:
        RuntimeError: If clone or score step fails (critical steps).
    """
    cb: StepCallback = on_step if on_step is not None else _noop
    repo_url = repo_url.strip()
    logger.info("Agentic ADK pipeline starting for: %s", repo_url)

    runner = InMemoryRunner(agent=judge_agent)

    # run_pipeline() is always called from asyncio.to_thread in the SSE endpoint,
    # so no event loop is running on this thread and asyncio.run() is safe.
    try:
        final_output = asyncio.run(_run_workflow(runner, repo_url, cb))
    except RuntimeError:
        raise   # critical step failure — already labelled by wrapper
    except Exception as exc:
        raise RuntimeError(f"ADK Agent execution failed for {repo_url}: {exc}") from exc

    verdict = Verdict(
        repo_url=repo_url,
        score=final_output.get("score", 0.0),
        rubric_breakdown=final_output.get("rubric_breakdown", {}),
        duplicate_flag=final_output.get("duplicate_flag", False),
        similarity_score=final_output.get("similarity_score", 0.0),
        timestamp=final_output.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        error=final_output.get("error") or None,
        doc_id=final_output.get("doc_id") or None,
    )
    logger.info("Agentic ADK pipeline complete for %s — score=%.1f", repo_url, verdict.score)
    return verdict


async def _run_workflow(runner: InMemoryRunner, repo_url: str, cb: StepCallback) -> dict:
    """
    Async helper: create a session, run the LlmAgent, and return the final session state.
    """
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="judging-copilot"
    )

    async for event in runner.run_async(
        user_id="judging-copilot",
        session_id=session.id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=f"Judge the repository: {repo_url}")],
        ),
        state_delta={
            "repo_url": repo_url,
            "on_step": cb,
        },
    ):
        # We can inspect events here for debugging
        pass

    # Retrieve the final session state from the session service to construct the Verdict
    updated_session = await runner.session_service.get_session(
        app_name=runner.app_name,
        user_id="judging-copilot",
        session_id=session.id,
    )
    return updated_session.state
