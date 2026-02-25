"""Chat route for RAG-style retrieval and Gemini generation."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Any

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

try:
    from google import genai
    from google.genai import errors as genai_errors
except ImportError:  # pragma: no cover - depends on installed packages
    genai = None  # type: ignore[assignment]
    genai_errors = None  # type: ignore[assignment]

from utils.embeddings import get_query_embedding
from utils.similarity import retrieve_top_k


load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])

VECTOR_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "vector_store.json"
RETRIEVAL_TOP_K = 3
SIMILARITY_THRESHOLD = 0.7
LLM_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
MAX_SESSION_MESSAGES = 5

NO_CONTEXT_FALLBACK = (
    "I don't know"
)

session_memory: dict[str, list[dict[str, str]]] = {}
session_memory_lock = Lock()

_client: Any | None = None
_client_api_key: str | None = None


def _normalize_model_name(model_name: str) -> str:
    """Accept both `models/...` and bare model names."""
    cleaned = model_name.strip()
    if cleaned.startswith("models/"):
        return cleaned.split("/", 1)[1]
    return cleaned


class ChatRequest(BaseModel):
    """Incoming chat payload."""

    model_config = ConfigDict(extra="forbid")

    sessionId: str | None = None
    message: str | None = None


class ChatResponse(BaseModel):
    """Outgoing chat payload."""

    reply: str
    retrievedChunks: int


class GeminiAPIError(Exception):
    """Raised when Gemini API returns an error response."""


class GeminiTimeoutError(GeminiAPIError):
    """Raised when Gemini API request times out."""


def _get_genai_client() -> Any:
    """Create/reuse Gemini client configured from environment."""
    global _client
    global _client_api_key

    if genai is None:
        raise GeminiAPIError(
            "google-genai is not installed. Install it to enable Gemini calls."
        )

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise GeminiAPIError("Gemini API key is not configured.")

    if _client is not None and _client_api_key == api_key:
        return _client

    try:
        _client = genai.Client(api_key=api_key)
        _client_api_key = api_key
    except Exception as exc:  # pragma: no cover - external SDK behavior
        raise GeminiAPIError(f"Failed to initialize Gemini client: {exc}") from exc

    return _client


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message and keep only the last MAX_SESSION_MESSAGES entries."""
    if role not in {"user", "assistant"}:
        return

    cleaned = content.strip()
    if not cleaned:
        return

    with session_memory_lock:
        messages = session_memory.setdefault(session_id, [])
        messages.append({"role": role, "content": cleaned})
        if len(messages) > MAX_SESSION_MESSAGES:
            session_memory[session_id] = messages[-MAX_SESSION_MESSAGES:]


def get_recent_messages(session_id: str, limit: int = 5) -> list[dict[str, str]]:
    """Return a copy of the most recent messages for a session."""
    if limit <= 0:
        return []

    with session_memory_lock:
        messages = session_memory.setdefault(session_id, [])
        return [message.copy() for message in messages[-limit:]]


def _format_history(history: list[dict[str, str]]) -> str:
    """Format prior messages for prompt injection."""
    if not history:
        return "No prior history."

    formatted_lines: list[str] = []
    for message in history:
        role = message.get("role", "user")
        content = message.get("content", "").strip()
        if not content:
            continue
        speaker = "Assistant" if role == "assistant" else "User"
        formatted_lines.append(f"{speaker}: {content}")

    return "\n".join(formatted_lines) if formatted_lines else "No prior history."


def _load_vector_store(path: Path = VECTOR_STORE_PATH) -> list[dict[str, Any]]:
    """Load vector store entries from disk."""
    if not path.exists():
        raise FileNotFoundError(f"Vector store file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("vector_store.json must contain a list.")

    return data


def _build_prompt(
    question: str,
    retrieved_chunks: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> str:
    """Build a grounded prompt from retrieved context and user question."""
    top_chunks = "\n\n".join(chunk.get("content", "") for chunk in retrieved_chunks)
    formatted_history = _format_history(history)
    return (
        "You are a helpful AI assistant.\n\n"
        "STRICT RULES:\n"
        "- Answer ONLY from provided context\n"
        "- Chat history is only for continuity\n"
        "- If answer not found -> say 'I don't know'\n\n"
        "CONTEXT:\n"
        f"{top_chunks}\n\n"
        "CHAT HISTORY:\n"
        f"{formatted_history}\n\n"
        "USER QUESTION:\n"
        f"{question}\n\n"
        "ANSWER:"
    )


def _extract_reply(response: Any) -> str:
    """Extract generated text from Gemini response."""
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None)
    if not isinstance(candidates, list):
        return ""

    text_segments: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None)
        if not isinstance(parts, list):
            continue
        for part in parts:
            piece = getattr(part, "text", None)
            if isinstance(piece, str) and piece.strip():
                text_segments.append(piece.strip())

    return "\n".join(text_segments).strip()


def _call_gemini_llm(prompt: str) -> str:
    """Call Gemini LLM through google-genai SDK and return generated text."""
    client = _get_genai_client()

    try:
        response = client.models.generate_content(
            model=_normalize_model_name(LLM_MODEL),
            contents=prompt,
            config={
                "temperature": 0.2,
                "max_output_tokens": 512,
            },
        )
    except Exception as exc:  # pragma: no cover - external SDK behavior
        message = str(exc)
        logger.error("Gemini chat API request failed: %s", message)
        api_error_type = getattr(genai_errors, "APIError", None)
        if api_error_type is not None and isinstance(exc, api_error_type):
            status = getattr(exc, "status", None)
            if status in (408, 504):
                raise GeminiTimeoutError("Gemini API request timed out.") from exc
            raise GeminiAPIError(f"Gemini API failure: {message}") from exc

        if "timeout" in message.lower() or "deadline" in message.lower():
            raise GeminiTimeoutError("Gemini API request timed out.") from exc
        raise GeminiAPIError(f"Gemini API failure: {message}") from exc

    reply = _extract_reply(response)
    if not reply:
        raise GeminiAPIError("Gemini API returned an empty response.")
    return reply


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a user message with retrieval-augmented generation."""
    session_id = (request.sessionId or "").strip()
    message = (request.message or "").strip()

    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required.")
    if not message:
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    with session_memory_lock:
        session_memory.setdefault(session_id, [])
    add_message(session_id, "user", message)
    history = get_recent_messages(session_id, limit=MAX_SESSION_MESSAGES)

    query_vector = get_query_embedding(message)
    if not query_vector:
        raise HTTPException(
            status_code=502,
            detail="Gemini API failure while generating query embedding.",
        )

    try:
        documents = _load_vector_store()
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Unable to load vector store: %s", exc)
        raise HTTPException(status_code=500, detail="Vector store is unavailable.") from exc

    retrieved = retrieve_top_k(
        query_vector=query_vector,
        documents=documents,
        k=RETRIEVAL_TOP_K,
        threshold=SIMILARITY_THRESHOLD,
    )
    if not retrieved:
        add_message(session_id, "assistant", NO_CONTEXT_FALLBACK)
        return ChatResponse(reply=NO_CONTEXT_FALLBACK, retrievedChunks=0)

    prompt = _build_prompt(
        question=message,
        retrieved_chunks=retrieved,
        history=history,
    )
    try:
        reply = _call_gemini_llm(prompt)
    except GeminiTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except GeminiAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    add_message(session_id, "assistant", reply)
    return ChatResponse(reply=reply, retrievedChunks=len(retrieved))
