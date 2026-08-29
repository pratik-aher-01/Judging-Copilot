"""
firestore_client.py — All Firestore read/write operations for Judging Copilot.

Responsibilities:
  - Initialize the Firebase Admin SDK once (singleton pattern)
  - Write a Verdict object to the Firestore 'verdicts' collection
  - Provide read helpers for querying past verdicts (future use)

Contract (backend-pipeline skill):
  Input : verdict: Verdict  (dataclass from agent/orchestrator.py)
  Output: doc_id: str       (the Firestore document ID of the written record)
  Raises: RuntimeError if Firestore write fails

Rules (AGENT.md conventions):
  - ONLY this module may write to Firestore — never from orchestrator.py directly
  - Credentials path comes from FIREBASE_CREDENTIALS_PATH env var — never hardcoded
  - Verdict fields written as-is; no transformation or filtering here
"""

import os


def _get_db():
    """
    Initialize and return the Firestore client (lazy singleton).

    Reads FIREBASE_CREDENTIALS_PATH from environment.

    Returns:
        google.cloud.firestore.Client instance.

    Raises:
        RuntimeError: If credentials path is missing or invalid.
    """
    # TODO:
    #   1. Read FIREBASE_CREDENTIALS_PATH from os.environ
    #   2. Call firebase_admin.initialize_app(credentials.Certificate(...)) once
    #   3. Return firestore.client()
    raise NotImplementedError("_get_db is not yet implemented")


def write_verdict(verdict) -> str:
    """
    Persist a Verdict to the Firestore 'verdicts' collection.

    Args:
        verdict: A Verdict dataclass instance from agent/orchestrator.py.

    Returns:
        doc_id (str): The auto-generated Firestore document ID.

    Raises:
        RuntimeError: If the write operation fails.
    """
    # TODO:
    #   1. db = _get_db()
    #   2. Convert verdict dataclass to dict (dataclasses.asdict)
    #   3. db.collection("verdicts").add(verdict_dict) → get doc ref + id
    #   4. Return doc_id
    raise NotImplementedError("write_verdict is not yet implemented")
