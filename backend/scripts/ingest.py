"""Ingest documents, chunk content, generate embeddings, and build a vector store."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent

# Allow running this file directly: `python backend/scripts/ingest.py`
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.chunking import chunk_text  # noqa: E402
from utils.embeddings import get_embedding  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

DEFAULT_DOCS_PATH = BACKEND_DIR / "data" / "docs.json"
DEFAULT_OUTPUT_PATH = BACKEND_DIR / "data" / "vector_store.json"


def load_docs(path: Path) -> list[dict[str, Any]]:
    """Load and validate document input JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, list):
        raise ValueError("docs.json must contain a top-level list of documents.")

    return payload


def build_vector_store(
    docs: list[dict[str, Any]],
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """Chunk documents and generate embeddings for each chunk."""
    vector_store: list[dict[str, Any]] = []

    for doc_index, doc in enumerate(docs, start=1):
        if not isinstance(doc, dict):
            logger.warning("Skipping document at index %d: expected object.", doc_index)
            continue

        doc_id = str(doc.get("id", f"unknown_{doc_index}"))
        title = str(doc.get("title", "Untitled"))
        content = doc.get("content", "")

        if not isinstance(content, str) or not content.strip():
            logger.warning("Skipping document '%s' (%s): empty or invalid content.", title, doc_id)
            continue

        chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        logger.info(
            "Document '%s' (%s): created %d chunk(s).",
            title,
            doc_id,
            len(chunks),
        )

        for chunk in chunks:
            vector = get_embedding(chunk)
            vector_store.append(
                {
                    "content": chunk,
                    "vector": vector,
                }
            )

    return vector_store


def save_vector_store(path: Path, vector_store: list[dict[str, Any]]) -> None:
    """Persist vector store JSON to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(vector_store, file, indent=2, ensure_ascii=False)


def ingest(
    docs_path: Path = DEFAULT_DOCS_PATH,
    output_path: Path = DEFAULT_OUTPUT_PATH,
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """Run full ingestion pipeline and write vector store to disk."""
    docs = load_docs(docs_path)
    vector_store = build_vector_store(docs, chunk_size=chunk_size, overlap=overlap)
    save_vector_store(output_path, vector_store)
    return vector_store


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for standalone execution."""
    parser = argparse.ArgumentParser(description="Build vector store from docs.json.")
    parser.add_argument(
        "--docs-path",
        type=Path,
        default=DEFAULT_DOCS_PATH,
        help=f"Path to input docs JSON (default: {DEFAULT_DOCS_PATH})",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output vector store JSON (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=300,
        help="Maximum words per chunk (default: 300).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Number of overlapping words between chunks (default: 50).",
    )
    return parser.parse_args()


def main() -> int:
    """Standalone script entry point."""
    args = parse_args()

    try:
        vector_store = ingest(
            docs_path=args.docs_path,
            output_path=args.output_path,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
    except Exception as exc:  # pragma: no cover - CLI safety net
        logger.error("Ingestion failed: %s", exc)
        return 1

    success_count = sum(1 for entry in vector_store if entry.get("vector"))
    failure_count = len(vector_store) - success_count
    logger.info(
        "Saved %d vector entries to %s (%d successful embeddings, %d failed).",
        len(vector_store),
        args.output_path,
        success_count,
        failure_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

