"""
clone_tool.py — Pipeline step 1: Clone a submission repository.

Contract (backend-pipeline skill):
  Input : repo_url: str
  Output: local_path: str  (absolute path to cloned repo on disk)
  Raises: RuntimeError — never returns a partial result; orchestrator catches and logs

Do NOT:
  - Call Gemini or Firestore
  - Be called directly from app.py — route through orchestrator.py

Implementation notes:
  - Uses subprocess (not gitpython's clone_from) for reliable cross-platform timeout.
    gitpython's kill_after_timeout does not work reliably on Windows when passed to
    clone_from. We clone with subprocess.run(timeout=CLONE_TIMEOUT_SECONDS) and then
    open the result with git.Repo() to validate the clone succeeded.
  - Creates a fresh temp directory per call; removes any pre-existing stale
    temp directory with the same derived name before starting.
"""

import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import uuid

import git  # gitpython — used only to validate the clone result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLONE_TIMEOUT_SECONDS = 60  # hard wall-clock limit for git clone subprocess
TEMP_DIR_PREFIX = "judging_copilot_clone_"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_url(repo_url: str) -> None:
    """
    Reject obviously malformed or non-GitHub URLs before attempting a clone.

    Accepts:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git

    Raises:
        RuntimeError: If the URL doesn't look like a public GitHub HTTPS URL.
    """
    pattern = r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(\.git)?/?$"
    if not re.match(pattern, repo_url.strip()):
        raise RuntimeError(
            f"Invalid repo URL: {repo_url!r}. "
            "Expected a public GitHub HTTPS URL, e.g. https://github.com/owner/repo"
        )


def _repo_slug(repo_url: str) -> str:
    """
    Derive a safe filesystem-friendly slug from a repo URL.

    e.g. "https://github.com/foo/bar.git" → "foo__bar"
    """
    path = repo_url.rstrip("/").rstrip(".git").split("github.com/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9_.-]", "_", path)


def _stale_clone_path(slug: str) -> Path:
    """Return the path where a previous clone of this repo would live."""
    return Path(tempfile.gettempdir()) / f"{TEMP_DIR_PREFIX}{slug}"


def _cleanup_stale(target: Path) -> None:
    """Remove a leftover temp directory from a previous failed run."""
    if target.exists():
        logger.info("Removing stale clone directory: %s", target)
        shutil.rmtree(target, ignore_errors=True)


def _cleanup_old_clones(slug: str) -> None:
    """
    Best-effort removal of any old clone directories for this slug.

    On Windows, shutil.rmtree can silently fail when file handles are still
    held (e.g. by a previous killed process). We no longer *depend* on this
    succeeding — each clone run uses a unique temp directory — but we clean up
    opportunistically to avoid accumulating stale dirs in %TEMP%.
    """
    tmp = Path(tempfile.gettempdir())
    for entry in tmp.glob(f"{TEMP_DIR_PREFIX}{slug}_*"):
        if entry.is_dir():
            logger.debug("Opportunistic cleanup of old clone dir: %s", entry)
            shutil.rmtree(entry, ignore_errors=True)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def clone_repo(repo_url: str) -> str:
    """
    Clone a public GitHub repository to a local temporary directory.

    Steps:
      1. Validate the URL (must be a public GitHub HTTPS URL)
      2. Remove any stale temp directory from a previous failed clone
      3. Run ``git clone <repo_url> <target>`` via subprocess with a 60-second timeout
      4. Verify the result is a valid git repository (gitpython sanity check)
      5. Return the absolute path to the cloned repository root

    Args:
        repo_url: Public GitHub HTTPS URL, e.g. "https://github.com/owner/repo".

    Returns:
        Absolute path (str) to the cloned repository root on disk.

    Raises:
        RuntimeError: On any of the following:
          - URL fails validation (not a GitHub HTTPS URL)
          - Clone times out after CLONE_TIMEOUT_SECONDS seconds
          - git subprocess exits with a non-zero return code
          - Clone directory is not a valid git repo after cloning
    """
    repo_url = repo_url.strip()
    _validate_url(repo_url)

    slug = _repo_slug(repo_url)

    # Step 2 — create a guaranteed-unique temp directory for this run.
    # Using mkdtemp + a unique suffix means we never collide with a leftover
    # directory from a previous run, even if shutil.rmtree failed silently on
    # Windows due to locked file handles.
    # We still attempt best-effort cleanup of old dirs, but never block on it.
    _cleanup_old_clones(slug)

    # mkdtemp creates and returns a directory that already exists — git clone
    # requires the target to NOT exist, so we remove the empty dir mkdtemp made
    # and pass the same path to git clone (which will re-create it).
    run_id = uuid.uuid4().hex[:8]
    target = Path(tempfile.mkdtemp(prefix=f"{TEMP_DIR_PREFIX}{slug}_{run_id}_"))
    # Remove the empty dir so git clone can create it
    target.rmdir()

    logger.info("Cloning %s → %s (timeout=%ds)", repo_url, target, CLONE_TIMEOUT_SECONDS)

    # Step 3 — subprocess clone with hard timeout
    cmd = ["git", "clone", "--depth", "1", repo_url, str(target)]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        # Clean up the partial clone so next run starts fresh
        _cleanup_stale(target)
        raise RuntimeError(
            f"git clone timed out after {CLONE_TIMEOUT_SECONDS}s for {repo_url}. "
            "The repository may be too large or the network too slow."
        )
    except FileNotFoundError:
        raise RuntimeError(
            "git executable not found. Ensure git is installed and on PATH."
        )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        _cleanup_stale(target)
        # Surface auth failures and bad URLs with a clear message
        if "Repository not found" in stderr or "not found" in stderr.lower():
            raise RuntimeError(
                f"Repository not found or is private: {repo_url}\n"
                f"git stderr: {stderr}"
            )
        if "Authentication failed" in stderr:
            raise RuntimeError(
                f"Authentication failed for {repo_url}. "
                "Only public repositories are supported.\n"
                f"git stderr: {stderr}"
            )
        raise RuntimeError(
            f"git clone failed (exit code {result.returncode}) for {repo_url}.\n"
            f"git stderr: {stderr}"
        )

    # Step 4 — sanity check: confirm it's a valid repo gitpython can open
    try:
        repo = git.Repo(str(target))
        _ = repo.head.commit  # touches the object store; raises if repo is broken
    except Exception as exc:
        _cleanup_stale(target)
        raise RuntimeError(
            f"Clone of {repo_url} succeeded but produced an invalid git repo: {exc}"
        ) from exc

    logger.info("Clone complete: %s", target)
    return str(target)
