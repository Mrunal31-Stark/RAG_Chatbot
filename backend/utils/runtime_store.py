"""In-memory runtime stores for auth, session memory, and user documents."""

from __future__ import annotations

from threading import Lock


users: dict[str, dict[str, str]] = {}
auth_sessions: dict[str, str] = {}
user_documents: dict[str, list[dict[str, object]]] = {}
session_memory: dict[str, list[dict[str, str]]] = {}

users_lock = Lock()
auth_sessions_lock = Lock()
user_documents_lock = Lock()
session_memory_lock = Lock()
