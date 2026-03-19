"""Lightweight in-memory authentication routes."""

from __future__ import annotations

from uuid import uuid4

import bcrypt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from utils.runtime_store import auth_sessions, auth_sessions_lock, users, users_lock


router = APIRouter(tags=["Auth"])


class AuthRequest(BaseModel):
    """Request payload for register/login."""

    model_config = ConfigDict(extra="forbid")

    username: str | None = None
    password: str | None = None


class AuthResponse(BaseModel):
    """Auth response payload."""

    sessionId: str
    username: str


def _validate_credentials(username: str | None, password: str | None) -> tuple[str, str]:
    cleaned_username = (username or "").strip()
    cleaned_password = (password or "").strip()

    if not cleaned_username:
        raise HTTPException(status_code=400, detail="username is required.")
    if not cleaned_password:
        raise HTTPException(status_code=400, detail="password is required.")

    return cleaned_username, cleaned_password


def _create_session(username: str) -> str:
    session_id = str(uuid4())
    with auth_sessions_lock:
        auth_sessions[session_id] = username
    return session_id


@router.post("/api/register", response_model=AuthResponse)
def register(request: AuthRequest) -> AuthResponse:
    """Register a user in the in-memory auth store."""
    username, password = _validate_credentials(request.username, request.password)

    with users_lock:
        if username in users:
            raise HTTPException(status_code=409, detail="username already exists.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        users[username] = {"password_hash": password_hash}

    session_id = _create_session(username)
    return AuthResponse(sessionId=session_id, username=username)


@router.post("/api/login", response_model=AuthResponse)
def login(request: AuthRequest) -> AuthResponse:
    """Authenticate a user from the in-memory auth store."""
    username, password = _validate_credentials(request.username, request.password)

    with users_lock:
        user = users.get(username)

    if user is None:
        raise HTTPException(status_code=401, detail="invalid username or password.")

    password_hash = user.get("password_hash", "")
    if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="invalid username or password.")

    session_id = _create_session(username)
    return AuthResponse(sessionId=session_id, username=username)
