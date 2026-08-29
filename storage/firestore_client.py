"""
firestore_client.py — All Firestore read/write operations for Judging Copilot.

This is the ONLY module in the project that touches Firestore.
All other modules must route through here — convention enforced by AGENT.md.

Contract (backend-pipeline skill):
  Input : verdict: Verdict  (dataclass from agent/orchestrator.py)
  Output: doc_id: str       (auto-generated Firestore document ID)
  Raises: RuntimeError if credentials are missing/invalid or write fails

Rules:
  - Firebase Admin SDK is initialized ONCE at module load (singleton via
    firebase_admin.get_app guard) — not per write call
  - FIREBASE_CREDENTIALS_PATH comes from environment — never hardcoded
  - Verdict is serialized with dataclasses.asdict — no manual field mapping
"""

import dataclasses
import logging
import os

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Firestore collection name
# ---------------------------------------------------------------------------

VERDICTS_COLLECTION = "verdicts"

# ---------------------------------------------------------------------------
# Singleton initialization — runs once when module is first imported
# ---------------------------------------------------------------------------

def _initialize_firebase() -> None:
    """
    Initialize the Firebase Admin SDK if it hasn't been initialized yet.

    Uses FIREBASE_CREDENTIALS_PATH from the environment. Safe to call
    multiple times — subsequent calls are no-ops if already initialized.

    Raises:
        RuntimeError: If FIREBASE_CREDENTIALS_PATH is unset, empty, or the
                      file does not exist / is not valid JSON credentials.
    """
    try:
        firebase_admin.get_app()
        return  # already initialized
    except ValueError:
        pass  # not yet initialized — proceed

    creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "").strip()
    if not creds_path:
        raise RuntimeError(
            "FIREBASE_CREDENTIALS_PATH environment variable is not set. "
            "Add it to your .env file (see .env.example)."
        )

    if not os.path.isfile(creds_path):
        raise RuntimeError(
            f"Firebase credentials file not found: {creds_path!r}. "
            "Check FIREBASE_CREDENTIALS_PATH in your .env file."
        )

    try:
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized from: %s", creds_path)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to initialize Firebase Admin SDK with credentials "
            f"at {creds_path!r}: {exc}"
        ) from exc


def _get_db():
    """
    Return a Firestore client, initializing Firebase if needed.

    Returns:
        google.cloud.firestore.Client instance.
    """
    _initialize_firebase()
    return firestore.client()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def write_verdict(verdict) -> str:
    """
    Persist a Verdict to the Firestore 'verdicts' collection.

    Converts the Verdict dataclass to a plain dict using dataclasses.asdict,
    then writes it as a new auto-ID document. The 'error' field is included
    only if it is not None (keeps documents clean for clean verdicts).

    Args:
        verdict: A Verdict dataclass instance from agent/orchestrator.py.

    Returns:
        doc_id (str): The auto-generated Firestore document ID.

    Raises:
        RuntimeError: If Firebase initialization fails or the Firestore
                      write operation fails for any reason.
    """
    try:
        db = _get_db()
    except RuntimeError:
        raise  # propagate credential errors as-is

    # Convert dataclass → dict; drop the 'error' field if None to keep docs clean
    try:
        verdict_dict = dataclasses.asdict(verdict)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to serialize Verdict to dict: {exc}"
        ) from exc

    if verdict_dict.get("error") is None:
        verdict_dict.pop("error", None)

    try:
        _time, doc_ref = db.collection(VERDICTS_COLLECTION).add(verdict_dict)
        doc_id = doc_ref.id
        logger.info(
            "Verdict written to Firestore: collection=%s, doc_id=%s, "
            "repo=%s, score=%.1f",
            VERDICTS_COLLECTION, doc_id,
            verdict_dict.get("repo_url", "?"),
            verdict_dict.get("score", 0.0),
        )
        return doc_id
    except Exception as exc:
        raise RuntimeError(
            f"Firestore write failed for {verdict_dict.get('repo_url', '?')}: {exc}"
        ) from exc


def list_verdicts(limit: int = 100) -> list[dict]:
    """
    Return all verdict documents from Firestore, most recent first.

    Args:
        limit: Maximum number of documents to return (default 100).

    Returns:
        List of dicts, each including Firestore doc ID under the key '_doc_id'.

    Raises:
        RuntimeError: If Firestore query fails.
    """
    try:
        db = _get_db()
        docs = (
            db.collection(VERDICTS_COLLECTION)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["_doc_id"] = doc.id
            results.append(data)
        logger.debug("list_verdicts returned %d documents", len(results))
        return results
    except Exception as exc:
        raise RuntimeError(f"Firestore list_verdicts failed: {exc}") from exc


def get_verdict(doc_id: str) -> dict:
    """
    Return a single verdict document by its Firestore document ID.

    Args:
        doc_id: Firestore document ID string.

    Returns:
        Dict of the verdict document fields, including '_doc_id'.

    Raises:
        KeyError: If no document with that ID exists in the verdicts collection.
        RuntimeError: If Firestore query fails.
    """
    try:
        db = _get_db()
        doc = db.collection(VERDICTS_COLLECTION).document(doc_id).get()
    except Exception as exc:
        raise RuntimeError(
            f"Firestore get_verdict failed for doc_id={doc_id!r}: {exc}"
        ) from exc

    if not doc.exists:
        raise KeyError(f"No verdict found with doc_id={doc_id!r}")

    data = doc.to_dict()
    data["_doc_id"] = doc.id
    return data
