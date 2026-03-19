"""User document upload route for chunking and embedding generation."""

from __future__ import annotations

from io import BytesIO
import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from pypdf import PdfReader

from utils.chunking import chunk_text
from utils.embeddings import get_embedding
from utils.runtime_store import (
    auth_sessions,
    auth_sessions_lock,
    get_user_documents_for_session,
    resolve_document_owner,
    save_user_documents,
    user_documents,
    user_documents_lock,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload"])

ALLOWED_TEXT_EXTENSIONS = {".txt", ".md"}
ALLOWED_PDF_EXTENSIONS = {".pdf"}


class UploadResponse(BaseModel):
    """Response payload for upload processing."""

    message: str
    chunksAdded: int


def _validate_session(session_id: str) -> None:
    with auth_sessions_lock:
        if session_id not in auth_sessions:
            raise HTTPException(status_code=401, detail="invalid sessionId.")


def _extract_text(upload: UploadFile, raw_bytes: bytes) -> str:
    filename = upload.filename or ""
    extension = Path(filename).suffix.lower()
    content_type = (upload.content_type or "").lower()

    if extension in ALLOWED_PDF_EXTENSIONS or content_type == "application/pdf":
        reader = PdfReader(BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(page for page in pages if page.strip())

    if extension in ALLOWED_TEXT_EXTENSIONS or content_type.startswith("text/"):
        return raw_bytes.decode("utf-8", errors="ignore")

    raise HTTPException(status_code=400, detail="only PDF and text files are supported.")


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines).strip()


@router.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    sessionId: str = Form(...),
) -> UploadResponse:
    """Upload, chunk, embed, and store a user document."""
    session_id = sessionId.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="sessionId is required.")

    _validate_session(session_id)

    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="uploaded file is empty.")

    try:
        text = _extract_text(file, raw_bytes)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - parsing depends on file contents
        logger.error("Failed to extract uploaded document text: %s", exc)
        raise HTTPException(status_code=400, detail="failed to process uploaded file.") from exc

    cleaned_text = _clean_text(text)
    if not cleaned_text:
        raise HTTPException(status_code=400, detail="uploaded file contains no readable text.")

    chunks = chunk_text(cleaned_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="uploaded file did not produce any chunks.")

    chunk_records: list[dict[str, object]] = []
    for chunk in chunks:
        vector = get_embedding(chunk)
        if vector:
            chunk_records.append({"content": chunk, "vector": vector})

    if not chunk_records:
        raise HTTPException(
            status_code=502,
            detail="embedding generation failed for uploaded document.",
        )

    owner_key = resolve_document_owner(session_id)
    with user_documents_lock:
        bucket = user_documents.setdefault(owner_key, [])
        bucket.extend(chunk_records)
    save_user_documents()

    logger.info(
        "Indexed %s chunks for owner '%s' (session '%s'). Total user chunks: %s",
        len(chunk_records),
        owner_key,
        session_id,
        len(get_user_documents_for_session(session_id)),
    )

    return UploadResponse(
        message="Document uploaded and indexed successfully.",
        chunksAdded=len(chunk_records),
    )
