import os
import sys
from unittest.mock import MagicMock, patch
from google.genai import errors
import httpx
import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.rag.ingestion.embeddings import (
    GeminiEmbeddingProvider,
    JinaEmbeddingProvider,
    get_embedding_provider,
)
from app.rag.ingestion.pipeline import (
    _embed_batch_with_retry,
    _embedding_rate_limiter,
    _is_retryable_embedding_error,
)


def test_gemini_provider_documents():
    mock_resp = MagicMock()
    mock_emb1 = MagicMock(values=[0.1] * 768)
    mock_emb2 = MagicMock(values=[0.2] * 768)
    mock_resp.embeddings = [mock_emb1, mock_emb2]

    provider = GeminiEmbeddingProvider(api_key="fake_key")
    with patch.object(provider.client.models, "embed_content", return_value=mock_resp) as mock_embed:
        res = provider.embed_documents(["doc 1", "doc 2"])
        assert len(res) == 2
        assert len(res[0]) == 768
        assert len(res[1]) == 768

        # Assert config
        call_kwargs = mock_embed.call_args[1]
        assert call_kwargs["contents"] == ["doc 1", "doc 2"]
        assert call_kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"
        assert call_kwargs["config"].output_dimensionality == 768


def test_gemini_provider_query():
    mock_resp = MagicMock()
    mock_resp.embeddings = [MagicMock(values=[0.3] * 768)]

    provider = GeminiEmbeddingProvider(api_key="fake_key")
    with patch.object(provider.client.models, "embed_content", return_value=mock_resp) as mock_embed:
        res = provider.embed_query("query test")
        assert len(res) == 768

        call_kwargs = mock_embed.call_args[1]
        assert call_kwargs["contents"] == "query test"
        assert call_kwargs["config"].task_type == "RETRIEVAL_QUERY"
        assert call_kwargs["config"].output_dimensionality == 768


def test_jina_provider_documents_index_ordering():
    provider = JinaEmbeddingProvider(api_key="jina_fake_key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    # Return out of order: index 1 before index 0
    mock_resp.json.return_value = {
        "data": [
            {"index": 1, "embedding": [0.2] * 768},
            {"index": 0, "embedding": [0.1] * 768},
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = provider.embed_documents(["First document", "Second document"])

        assert len(res) == 2
        # Assert returned order corresponds to index 0 then index 1
        assert res[0] == [0.1] * 768
        assert res[1] == [0.2] * 768

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["task"] == "retrieval.passage"
        assert call_kwargs["json"]["dimensions"] == 768
        assert call_kwargs["json"]["input"] == ["First document", "Second document"]


def test_jina_provider_query():
    provider = JinaEmbeddingProvider(api_key="jina_fake_key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "data": [
            {"index": 0, "embedding": [0.9] * 768},
        ]
    }

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        res = provider.embed_query("search query")
        assert len(res) == 768
        assert res[0] == 0.9

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["task"] == "retrieval.query"
        assert call_kwargs["json"]["dimensions"] == 768
        assert call_kwargs["json"]["input"] == ["search query"]


def test_get_embedding_provider_dynamic():
    # 1. Default / Gemini
    with patch.object(settings, "EMBEDDING_PROVIDER", "gemini"):
        prov = get_embedding_provider()
        assert isinstance(prov, GeminiEmbeddingProvider)

    # 2. Jina with key
    with patch.object(settings, "EMBEDDING_PROVIDER", "jina"), \
         patch.object(settings, "JINA_API_KEY", "fake_jina_key"):
        prov = get_embedding_provider()
        assert isinstance(prov, JinaEmbeddingProvider)
        assert prov.api_key == "fake_jina_key"

    # 3. Jina without key falls back to Gemini
    with patch.object(settings, "EMBEDDING_PROVIDER", "jina"), \
         patch.object(settings, "JINA_API_KEY", None):
        prov = get_embedding_provider()
        assert isinstance(prov, GeminiEmbeddingProvider)


def test_is_retryable_embedding_error():
    # Transient HTTP errors (Jina or Gemini)
    for code in (429, 500, 502, 503, 504):
        err = httpx.HTTPStatusError(f"{code} Error", request=MagicMock(), response=MagicMock(status_code=code))
        assert _is_retryable_embedding_error(err) is True

    # Non-retryable HTTP errors
    for code in (400, 401, 403, 404):
        err = httpx.HTTPStatusError(f"{code} Error", request=MagicMock(), response=MagicMock(status_code=code))
        assert _is_retryable_embedding_error(err) is False

    # Timeout and network errors
    assert _is_retryable_embedding_error(httpx.ConnectTimeout("timeout")) is True
    assert _is_retryable_embedding_error(httpx.NetworkError("network fail")) is True
    assert _is_retryable_embedding_error(TimeoutError()) is True

    # Google GenAI API errors
    mock_api_err_429 = errors.APIError(429, "Rate limit")
    assert _is_retryable_embedding_error(mock_api_err_429) is True

    mock_api_err_400 = errors.APIError(400, "Bad Request")
    assert _is_retryable_embedding_error(mock_api_err_400) is False


def test_rate_limiter_called_in_embed_batch_with_retry():
    mock_provider = MagicMock()
    mock_provider.embed_documents.return_value = [[0.1] * 768]
    mock_provider.model = "test-model"

    with patch.object(_embedding_rate_limiter, "acquire") as mock_acquire:
        res = _embed_batch_with_retry(
            mock_provider,
            ["sample chunk text"],
            estimated_tokens=55,
        )

        # Assert acquire is called with estimated_tokens
        mock_acquire.assert_called_once_with(55)
        # Assert provider.embed_documents is delegated to
        mock_provider.embed_documents.assert_called_once_with(["sample chunk text"])
        assert len(res) == 1

