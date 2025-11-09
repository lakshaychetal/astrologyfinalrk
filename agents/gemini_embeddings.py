"""Gemini embedding utilities used by the smart orchestrator.

Compared to the legacy ``EmbeddingsRetriever`` this module exposes both query
and document embedding helpers, keeps everything at 768 dimensions, and adds a
simple cosine-similarity helper so callers can post-filter candidate passages.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class EmbeddedText:
    """Container returned for each embedding request."""

    text: str
    embedding: Sequence[float]
    model: str
    dimension: int
    latency_ms: float


class GeminiEmbeddings:
    """Wraps ``text-embedding-004`` with convenience helpers."""

    def __init__(self, project_id: str, location: str, model: str = "text-embedding-004", dimension: int = 768):
        self.project_id = project_id
        self.location = location
        self.model = model
        self.dimension = dimension
        self.client = genai.Client(vertexai=True, project=project_id, location=location)
        logger.info("GeminiEmbeddings ready: model=%s dim=%d", self.model, self.dimension)

    def embed_query(self, text: str) -> EmbeddedText:
        """Embed a single retrieval query."""

        return self.embed_queries_batch([text])[0]

    def embed_queries(self, texts: Iterable[str]) -> List[dict]:
        """Compat layer for legacy callers expecting dict payloads."""

        results = []
        for embedded in self.embed_queries_batch(texts):
            results.append(
                {
                    "query": embedded.text,
                    "embedding": embedded.embedding,
                    "dimension": embedded.dimension,
                    "embedding_model": embedded.model,
                    "execution_time_ms": embedded.latency_ms,
                }
            )
        return results

    def embed_document(self, text: str) -> EmbeddedText:
        """Embed a document chunk for storage or offline indexing."""

        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=self.dimension)
        )
        values = response.embeddings[0].values if hasattr(response, "embeddings") else response.embedding
        return EmbeddedText(text, values, self.model, len(values), 0.0)

    def embed_queries_batch(self, texts: Iterable[str]) -> List[EmbeddedText]:
        """Embed a collection of texts, returning ``EmbeddedText`` objects."""

        results: List[EmbeddedText] = []
        for text in texts:
            if not text:
                continue
            with _latency() as timer:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config=types.EmbedContentConfig(output_dimensionality=self.dimension)
                )
            values = response.embeddings[0].values if hasattr(response, "embeddings") else response.embedding
            results.append(EmbeddedText(text, values, self.model, len(values), timer.elapsed_ms))
        return results

    @staticmethod
    def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        """Compute cosine similarity between two embedding vectors."""

        a = np.array(vec_a)
        b = np.array(vec_b)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)


class _latency:
    """Context manager to time embedding calls."""

    def __enter__(self):
        import time

        self._start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        self.elapsed_ms = (time.time() - self._start) * 1000
        return False

__all__ = ["GeminiEmbeddings", "EmbeddedText"]
