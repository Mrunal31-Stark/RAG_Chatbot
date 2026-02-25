"""Gemini embedding helpers using the google-genai SDK."""

from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:  # pragma: no cover - depends on environment package install
    genai = None  # type: ignore[assignment]


load_dotenv()

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"

_client: Any | None = None
_client_api_key: str | None = None


def _get_client() -> Any | None:
    """Create/reuse a Gemini client configured with env API key."""
    global _client
    global _client_api_key

    if genai is None:
        logger.error("google-genai is not installed. Install it to enable embeddings.")
        return None

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error(
            "Gemini API key not found. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in .env."
        )
        return None

    if _client is not None and _client_api_key == api_key:
        return _client

    try:
        _client = genai.Client(api_key=api_key)
        _client_api_key = api_key
    except Exception as exc:  # pragma: no cover - external SDK behavior
        logger.error("Failed to initialize Gemini client: %s", exc)
        return None

    return _client


def _to_float_list(values: Any) -> list[float]:
    """Convert raw embedding values to list[float]."""
    if not isinstance(values, list) or not values:
        return []

    try:
        return [float(value) for value in values]
    except (TypeError, ValueError):
        logger.error("Gemini embedding response contains non-numeric values.")
        return []


def _extract_embedding_values(response: Any) -> list[float]:
    """Extract embedding values from google-genai response payload."""
    embedding = getattr(response, "embedding", None)
    if embedding is not None:
        values = getattr(embedding, "values", None)
        normalized = _to_float_list(values)
        if normalized:
            return normalized

    embeddings = getattr(response, "embeddings", None)
    if isinstance(embeddings, list) and embeddings:
        values = getattr(embeddings[0], "values", None)
        normalized = _to_float_list(values)
        if normalized:
            return normalized

    if isinstance(response, dict):
        embedding_dict = response.get("embedding")
        if isinstance(embedding_dict, dict):
            normalized = _to_float_list(embedding_dict.get("values"))
            if normalized:
                return normalized

        embeddings_list = response.get("embeddings")
        if isinstance(embeddings_list, list) and embeddings_list:
            first = embeddings_list[0]
            if isinstance(first, dict):
                normalized = _to_float_list(first.get("values"))
                if normalized:
                    return normalized

    return []


def _embed(text: str, task_type: str) -> list[float]:
    """Generate embedding for text with task-specific retrieval mode."""
    if not isinstance(text, str):
        logger.error("Embedding input must be a string.")
        return []

    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    client = _get_client()
    if client is None:
        return []

    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=cleaned_text,
            config={"task_type": task_type},
        )
    except Exception as exc:  # pragma: no cover - external SDK behavior
        logger.error("Embedding error: %s", exc)
        return []

    embedding = _extract_embedding_values(response)
    if not embedding:
        logger.error("Gemini embedding response is empty or malformed.")
    return embedding


def get_embedding(text: str) -> list[float]:
    """Generate document embedding vector."""
    return _embed(text=text, task_type="RETRIEVAL_DOCUMENT")


def get_query_embedding(text: str) -> list[float]:
    """Generate query embedding vector."""
    return _embed(text=text, task_type="RETRIEVAL_QUERY")