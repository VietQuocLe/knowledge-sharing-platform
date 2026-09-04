from __future__ import annotations

import logging
import threading
import time
from typing import Any, Protocol

from google import genai
from google.genai import errors, types
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.observability import observe_llm, update_current_observation

logger = logging.getLogger(__name__)

# Global semaphore to serialize all Gemini Embedding API calls (single-thread)
_EMBEDDING_SEMAPHORE = threading.Semaphore(1)


class EmbeddingRateLimiter:
    """
    Sliding-window rate and token limiter for Gemini Embedding API.
    Tracks both (a) request count (RPM) and (b) token consumption (TPM) in a sliding window.
    """

    def __init__(self, window_seconds: float | None = None):
        self.window_seconds = window_seconds if window_seconds is not None else settings.ACTIVE_EMBEDDING_WINDOW_SECONDS
        self._history: list[tuple[float, int]] = []  # List of (timestamp, token_count)
        self._lock = threading.Lock()

    def acquire(self, estimated_tokens: int) -> None:
        """
        Blocks until capacity (RPM and TPM) is available within the sliding window,
        then records the new request and token allocation.
        """
        rpm_limit = settings.ACTIVE_EMBEDDING_RPM_LIMIT
        tpm_limit = settings.ACTIVE_EMBEDDING_TPM_LIMIT

        while True:
            with self._lock:
                now = time.time()
                cutoff = now - self.window_seconds

                # Clean up entries older than sliding window
                self._history = [entry for entry in self._history if entry[0] > cutoff]

                current_requests = len(self._history)
                current_tokens = sum(tokens for _, tokens in self._history)

                # Check RPM & TPM limits
                if (current_requests + 1 > rpm_limit) or (current_tokens + estimated_tokens > tpm_limit):
                    if self._history:
                        oldest_time, _ = self._history[0]
                        sleep_time = max(0.1, (oldest_time + self.window_seconds) - now + 0.1)
                    else:
                        sleep_time = 1.0
                else:
                    # Capacity available: record and proceed
                    self._history.append((now, estimated_tokens))
                    return

            logger.info(
                f"EmbeddingRateLimiter: pacing for {sleep_time:.2f}s "
                f"(requests: {current_requests}/{rpm_limit}, tokens: {current_tokens + estimated_tokens}/{tpm_limit})"
            )
            time.sleep(sleep_time)


# Global singleton instance of rate limiter
_embedding_rate_limiter = EmbeddingRateLimiter()


def get_genai_client() -> genai.Client:
    """
    Initializes Google GenAI Client with settings.GOOGLE_API_KEY.
    """
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


def _is_retryable_embedding_error(exception: BaseException) -> bool:
    """
    Identifies retryable exceptions for Embedding calls (Gemini & Jina):
    - 429 ClientError (Rate limit / Resource exhausted)
    - 5xx ServerError (500 Internal, 502 Bad Gateway, 503 Unavailable, 504 Gateway Timeout)
    - Network / Connection / Timeout exceptions
    All other exceptions (400 Bad Request, 401 Auth, 403 Forbidden, 404, etc.) are non-retryable.
    """
    if isinstance(exception, errors.APIError):
        if exception.code == 429 or (exception.code and 500 <= exception.code < 600):
            return True
        return False
    if isinstance(exception, httpx.HTTPStatusError):
        if exception.response.status_code == 429 or (500 <= exception.response.status_code < 600):
            return True
        return False
    if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError, TimeoutError, ConnectionError)):
        return True
    return False


# Backward compatibility alias
_is_retryable_gemini_error = _is_retryable_embedding_error


@observe_llm(name="generate_embeddings_batch", as_type="generation")
@retry(
    retry=retry_if_exception(_is_retryable_embedding_error),
    stop=stop_after_attempt(settings.GEMINI_EMBEDDING_RETRY_ATTEMPTS),
    wait=wait_exponential(
        multiplier=settings.GEMINI_EMBEDDING_RETRY_MULTIPLIER,
        min=settings.GEMINI_EMBEDDING_RETRY_MIN_WAIT,
        max=settings.GEMINI_EMBEDDING_RETRY_MAX_WAIT,
    ),
    reraise=True,
)
def _embed_batch_with_retry(
    provider_or_client: Any,
    contents: list[str],
    estimated_tokens: int = 0,
) -> list[list[float]]:
    """
    Calls embedding service with exponential backoff retry for transient/rate-limit errors.
    Acquires rate limiter capacity immediately before sending the API request.
    Supports both EmbeddingProvider and legacy genai.Client.
    """
    if estimated_tokens <= 0:
        estimated_tokens = sum(max(1, int(len(c.split()) * 1.3)) for c in contents)

    _embedding_rate_limiter.acquire(estimated_tokens)

    if hasattr(provider_or_client, "embed_documents"):
        embeddings = provider_or_client.embed_documents(contents)
    else:
        # Legacy genai.Client fallback
        response = provider_or_client.models.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            contents=contents,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.EMBEDDING_DIMENSION,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )
        embeddings = [emb.values for emb in response.embeddings]

    update_current_observation(
        model=getattr(provider_or_client, "model", settings.GEMINI_EMBEDDING_MODEL),
        input={"chunks_count": len(contents)},
        usage={"total_tokens": estimated_tokens},
        metadata={"batch_size": len(contents), "estimated_tokens": estimated_tokens},
    )

    return embeddings


class EmbeddingProvider(Protocol):
    """
    Protocol defining the strategy interface for text embedding providers.
    Supports both batch document embedding and single query embedding.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embeds a batch of document chunks.
        Returns a list of 768-dimensional float vectors matching the input texts order.
        """
        ...

    def embed_query(self, text: str) -> list[float]:
        """
        Embeds a single query string.
        Returns a 768-dimensional float vector.
        """
        ...


class GeminiEmbeddingProvider:
    """
    Default embedding provider utilizing Google GenAI SDK.
    Uses task_type='RETRIEVAL_DOCUMENT' for document chunks and 'RETRIEVAL_QUERY' for search queries.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.model = model or settings.GEMINI_EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.client = genai.Client(api_key=self.api_key)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=self.dimension,
                task_type="RETRIEVAL_DOCUMENT",
            ),
        )
        return [emb.values for emb in response.embeddings]

    def embed_query(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=self.dimension,
                task_type="RETRIEVAL_QUERY",
            ),
        )
        return response.embeddings[0].values


class JinaEmbeddingProvider:
    """
    Alternative embedding provider utilizing Jina Embeddings v3 REST API.
    Model: jina-embeddings-v3
    Uses task='retrieval.passage' for document chunks and 'retrieval.query' for search queries.
    Dimensions: 768 (matching the VECTOR(768) database schema).
    Guarantees index preservation by sorting on returned data items.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "jina-embeddings-v3",
        dimension: int = 768,
        timeout: float = 15.0,
        api_url: str = "https://api.jina.ai/v1/embeddings",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.timeout = timeout
        self.api_url = api_url

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "task": "retrieval.passage",
            "dimensions": self.dimension,
            "normalized": True,
            "input": texts,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            res_json = response.json()

        data = res_json.get("data", [])
        # Sort by returned index to strictly guarantee input order alignment
        sorted_data = sorted(data, key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    def embed_query(self, text: str) -> list[float]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "task": "retrieval.query",
            "dimensions": self.dimension,
            "normalized": True,
            "input": [text],
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            res_json = response.json()

        data = res_json.get("data", [])
        if not data:
            raise RuntimeError("Jina embedding response returned empty data list for query.")
        return data[0]["embedding"]


def get_embedding_provider() -> EmbeddingProvider:
    """
    Factory creating the active EmbeddingProvider instance based on runtime settings.
    Evaluated dynamically on every call (NOT cached) to allow seamless switching
    and dynamic patching in tests without stale state.
    """
    provider_name = (settings.EMBEDDING_PROVIDER or "gemini").lower()
    if provider_name == "jina":
        if not settings.JINA_API_KEY:
            logger.warning(
                "EMBEDDING_PROVIDER is set to 'jina' but JINA_API_KEY is missing. "
                "Falling back to GeminiEmbeddingProvider."
            )
            return GeminiEmbeddingProvider()
        return JinaEmbeddingProvider(
            api_key=settings.JINA_API_KEY,
            model=settings.JINA_EMBEDDING_MODEL,
            dimension=settings.EMBEDDING_DIMENSION,
            timeout=settings.JINA_EMBEDDING_TIMEOUT_SECONDS,
        )

    return GeminiEmbeddingProvider()


__all__ = [
    "_EMBEDDING_SEMAPHORE",
    "EmbeddingRateLimiter",
    "_embedding_rate_limiter",
    "get_genai_client",
    "_is_retryable_gemini_error",
    "_is_retryable_embedding_error",
    "_embed_batch_with_retry",
    "EmbeddingProvider",
    "GeminiEmbeddingProvider",
    "JinaEmbeddingProvider",
    "get_embedding_provider",
]
