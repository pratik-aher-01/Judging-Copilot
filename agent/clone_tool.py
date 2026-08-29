"""
clone_tool.py — Pipeline step 1: Clone a submission repository.

Responsibilities:
  - Accept a public GitHub repo_url
  - Clone it to a local temp directory
  - Return the local path as a string for downstream steps

Contract (backend-pipeline skill):
  Input : repo_url: str
  Output: local_path: str  (absolute path to cloned repo)
  Raises: RuntimeError if clone fails (bad URL, network error, auth)

Do NOT:
  - Call Gemini or Firestore
  - Be called directly from app.py — use orchestrator.py
"""

import tempfile


def clone_repo(repo_url: str) -> str:
    """
    Clone a public GitHub repository to a temporary local directory.

    Args:
        repo_url: Public GitHub URL, e.g. "https://github.com/owner/repo".

    Returns:
        Absolute path (str) to the cloned repository root on disk.

    Raises:
        RuntimeError: If the clone operation fails for any reason.
    """
    # TODO: use gitpython (git.Repo.clone_from) to clone repo_url into a
    #       tempfile.mkdtemp() directory, then return that path.
    raise NotImplementedError("clone_repo is not yet implemented")
