"""Runtime stores for auth, session memory, and user documents."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any


users: dict[str, dict[str, str]] = {}
auth_sessions: dict[str, str] = {}
session_memory: dict[str, list[dict[str, str]]] = {}

users_lock = Lock()
auth_sessions_lock = Lock()
session_memory_lock = Lock()

logger = logging.getLogger(__name__)

USER_DOCUMENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "user_documents.json"


def _load_user_documents() -> dict[str, list[dict[str, object]]]:
    """Load persisted user document chunks from disk."""
    if not USER_DOCUMENTS_PATH.exists():
        return {}

    try:
        with USER_DOCUMENTS_PATH.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load persisted user documents: %s", exc)
        return {}

    if not isinstance(payload, dict):
        logger.error("Persisted user documents must be a JSON object.")
        return {}

    hydrated: dict[str, list[dict[str, object]]] = {}
    for owner_key, items in payload.items():
        if not isinstance(owner_key, str) or not isinstance(items, list):
            continue

        normalized_items: list[dict[str, object]] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            content = item.get("content")
            vector = item.get("vector")
            if isinstance(content, str) and isinstance(vector, list):
                normalized_items.append({"content": content, "vector": vector})

        if normalized_items:
            hydrated[owner_key] = normalized_items

    return hydrated


user_documents: dict[str, list[dict[str, object]]] = _load_user_documents()
user_documents_lock = Lock()


def save_user_documents() -> None:
    """Persist indexed user documents so uploads survive server restarts."""
    with user_documents_lock:
        snapshot = {
            owner_key: [dict(item) for item in items]
            for owner_key, items in user_documents.items()
        }

    USER_DOCUMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with USER_DOCUMENTS_PATH.open("w", encoding="utf-8") as file:
            json.dump(snapshot, file, indent=2)
    except OSError as exc:
        logger.error("Failed to save user documents: %s", exc)


def resolve_document_owner(session_id: str) -> str:
    """Resolve a stable owner key for document storage and retrieval."""
    cleaned_session_id = session_id.strip()
    if not cleaned_session_id:
        return ""

    with auth_sessions_lock:
        return auth_sessions.get(cleaned_session_id, cleaned_session_id)


def get_user_documents_for_session(session_id: str) -> list[dict[str, Any]]:
    """Return user-scoped chunks for a session, including legacy session-keyed data."""
    owner_key = resolve_document_owner(session_id)
    candidate_keys = [cleaned for cleaned in {owner_key, session_id.strip()} if cleaned]

    scoped_documents: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()

    with user_documents_lock:
        for candidate_key in candidate_keys:
            for item in user_documents.get(candidate_key, []):
                content = str(item.get("content", ""))
                vector = json.dumps(item.get("vector", []), separators=(",", ":"))
                dedupe_key = (content, vector)
                if dedupe_key in seen_keys:
                    continue

                seen_keys.add(dedupe_key)
                scoped_documents.append(dict(item))

    return scoped_documents
