from __future__ import annotations

from functools import lru_cache
import logging
from typing import Any, Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class RerankerProvider(Protocol):
    """
    Protocol defining the interface for document reranking providers.
    Follows the Strategy Pattern.
    """

    def rerank(
        self, query: str, candidates: list[dict[str, Any]], top_n: int
    ) -> list[dict[str, Any]]:
        """
        Reranks a list of candidate dictionaries based on query relevance.
        Each candidate dict contains at least: {"chunk": AssetEmbedding, "rrf_score": float, ...}
        """
        ...


class NoOpProvider:
    """
    No-op provider that preserves existing candidate ordering (e.g. RRF score DESC)
    and slices the top_n items. Used as default when reranker is disabled or as fallback.
    """

    def rerank(
        self, query: str, candidates: list[dict[str, Any]], top_n: int
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []
        return candidates[:top_n]


class JinaRerankProvider:
    """
    Reranker implementation using Jina AI Rerank v2 API.
    Model: jina-reranker-v2-base-multilingual
    Resilient: On any network, timeout, HTTP, or parsing error,
    automatically falls back to NoOpProvider without raising exceptions.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "jina-reranker-v2-base-multilingual",
        timeout: float = 5.0,
        api_url: str = "https://api.jina.ai/v1/rerank",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.api_url = api_url
        self.fallback_provider = NoOpProvider()

    def rerank(
        self, query: str, candidates: list[dict[str, Any]], top_n: int
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []

        # Edge case: Avoid HTTP 400 from Jina when fewer candidates than requested top_n
        actual_top_n = min(top_n, len(candidates))

        # Extract text content from candidate chunks
        documents = [c["chunk"].content for c in candidates]

        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": actual_top_n,
            "return_documents": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

            results = data.get("results", [])
            reranked: list[dict[str, Any]] = []

            for item in results:
                cand_idx = item["index"]
                relevance_score = float(item["relevance_score"])
                cand = candidates[cand_idx]

                # Map rerank scores back to candidate
                cand["rerank_score"] = relevance_score
                cand["best_score"] = relevance_score
                reranked.append(cand)

            logger.info(
                "Jina rerank completed successfully: reranked %d candidates to top %d.",
                len(candidates),
                len(reranked),
            )
            return reranked

        except Exception as exc:
            logger.warning(
                "Jina rerank failed: %s. Falling back to NoOpProvider (preserving RRF order).",
                exc,
            )
            return self.fallback_provider.rerank(query, candidates, top_n)


def get_reranker() -> RerankerProvider:
    """
    Factory providing the active RerankerProvider instance based on current settings.
    Evaluates dynamically on each call so runtime setting changes (e.g. in tests) take effect immediately.
    If ENABLE_RERANKER is False or JINA_API_KEY is not configured, returns NoOpProvider.
    """
    if not settings.ENABLE_RERANKER or not settings.JINA_API_KEY:
        logger.info("Reranker is disabled or JINA_API_KEY missing. Using NoOpProvider.")
        return NoOpProvider()

    return JinaRerankProvider(
        api_key=settings.JINA_API_KEY,
        model=settings.JINA_RERANK_MODEL,
        timeout=settings.JINA_RERANK_TIMEOUT_SECONDS,
    )


__all__ = [
    "RerankerProvider",
    "NoOpProvider",
    "JinaRerankProvider",
    "get_reranker",
]

