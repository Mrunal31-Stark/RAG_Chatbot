"""Similarity and retrieval utilities for vector search."""

from __future__ import annotations

from typing import Any

import numpy as np


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Returns:
        Similarity score in [-1.0, 1.0]. Returns 0.0 for empty/zero-norm vectors.

    Raises:
        ValueError: If vectors are not the same length.
    """
    a = np.asarray(vec1, dtype=float)
    b = np.asarray(vec2, dtype=float)

    if a.size == 0 or b.size == 0:
        return 0.0
    if a.shape != b.shape:
        raise ValueError("vec1 and vec2 must have the same dimensions")

    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denominator == 0.0:
        return 0.0

    return float(np.dot(a, b) / denominator)


def retrieve_top_k(
    query_vector: list[float],
    documents: list[dict[str, Any]],
    k: int = 3,
    threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """Retrieve the top-k documents by cosine similarity.

    Each returned item includes:
    - content
    - vector
    - similarity
    """
    if k <= 0:
        return []
    if not documents:
        return []

    ranked: list[dict[str, Any]] = []

    for doc in documents:
        if not isinstance(doc, dict):
            continue

        vector = doc.get("vector")
        if not isinstance(vector, list) or not vector:
            continue

        try:
            score = cosine_similarity(query_vector, vector)
        except (ValueError, TypeError):
            continue

        if score < threshold:
            continue

        ranked.append(
            {
                "content": doc.get("content", ""),
                "vector": vector,
                "similarity": score,
            }
        )

    ranked.sort(key=lambda item: item["similarity"], reverse=True)
    return ranked[:k]

