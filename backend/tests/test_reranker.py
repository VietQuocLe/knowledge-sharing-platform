import os
import sys
from unittest.mock import MagicMock, patch
import httpx
import pytest

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.rag.retrieval.reranker import (
    NoOpProvider,
    JinaRerankProvider,
    get_reranker,
)


class DummyChunk:
    def __init__(self, id: int, content: str, asset_id: int = 1, page_number: int = 1, chunk_index: int = 0):
        self.id = id
        self.content = content
        self.asset_id = asset_id
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.token_count = 50


@pytest.fixture
def sample_candidates():
    return [
        {"chunk": DummyChunk(1, "Nội dung tài liệu học phần 1"), "rrf_score": 0.050, "best_score": 0.050},
        {"chunk": DummyChunk(2, "Nội dung tài liệu học phần 2"), "rrf_score": 0.040, "best_score": 0.040},
        {"chunk": DummyChunk(3, "Nội dung tài liệu học phần 3"), "rrf_score": 0.030, "best_score": 0.030},
        {"chunk": DummyChunk(4, "Nội dung tài liệu học phần 4"), "rrf_score": 0.020, "best_score": 0.020},
        {"chunk": DummyChunk(5, "Nội dung tài liệu học phần 5"), "rrf_score": 0.010, "best_score": 0.010},
        {"chunk": DummyChunk(6, "Nội dung tài liệu học phần 6"), "rrf_score": 0.005, "best_score": 0.005},
    ]


def test_noop_provider_empty():
    provider = NoOpProvider()
    assert provider.rerank("query", [], top_n=5) == []


def test_noop_provider_slices_top_n(sample_candidates):
    provider = NoOpProvider()
    result = provider.rerank("query", sample_candidates, top_n=3)
    assert len(result) == 3
    assert [c["chunk"].id for c in result] == [1, 2, 3]


def test_jina_rerank_success(sample_candidates):
    provider = JinaRerankProvider(api_key="mock_key")

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "results": [
            {"index": 2, "relevance_score": 0.95},
            {"index": 0, "relevance_score": 0.88},
            {"index": 1, "relevance_score": 0.65},
        ]
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        result = provider.rerank("query tìm kiếm", sample_candidates, top_n=3)

        assert mock_post.called
        assert len(result) == 3
        # Candidate 3 was ranked #1 by Jina
        assert result[0]["chunk"].id == 3
        assert result[0]["rerank_score"] == 0.95
        assert result[0]["best_score"] == 0.95

        # Candidate 1 was ranked #2
        assert result[1]["chunk"].id == 1
        assert result[1]["rerank_score"] == 0.88
        assert result[1]["best_score"] == 0.88

        # Candidate 2 was ranked #3
        assert result[2]["chunk"].id == 2
        assert result[2]["rerank_score"] == 0.65
        assert result[2]["best_score"] == 0.65


def test_jina_rerank_edge_case_fewer_candidates():
    provider = JinaRerankProvider(api_key="mock_key")
    few_candidates = [
        {"chunk": DummyChunk(1, "Text A"), "rrf_score": 0.1, "best_score": 0.1},
        {"chunk": DummyChunk(2, "Text B"), "rrf_score": 0.05, "best_score": 0.05},
    ]

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "results": [
            {"index": 1, "relevance_score": 0.9},
            {"index": 0, "relevance_score": 0.7},
        ]
    }

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        # Request top_n=5, but only 2 candidates exist
        result = provider.rerank("query", few_candidates, top_n=5)
        # Ensure payload sent top_n=2 to prevent HTTP 400 from Jina
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["top_n"] == 2
        assert len(result) == 2


def test_jina_rerank_fallback_on_network_or_http_error(sample_candidates):
    provider = JinaRerankProvider(api_key="mock_key")

    # Simulate timeout
    with patch("httpx.Client.post", side_effect=httpx.ConnectTimeout("Connection timed out")):
        result_timeout = provider.rerank("query", sample_candidates, top_n=3)
        # Must not raise exception, but fallback to NoOpProvider (RRF top 3)
        assert len(result_timeout) == 3
        assert [c["chunk"].id for c in result_timeout] == [1, 2, 3]

    # Simulate 500 Internal Server Error
    mock_err_res = MagicMock()
    mock_err_res.raise_for_status.side_effect = httpx.HTTPStatusError("500 Server Error", request=MagicMock(), response=MagicMock(status_code=500))
    with patch("httpx.Client.post", return_value=mock_err_res):
        result_500 = provider.rerank("query", sample_candidates, top_n=3)
        assert len(result_500) == 3
        assert [c["chunk"].id for c in result_500] == [1, 2, 3]


def test_get_reranker_disabled():
    with patch.object(settings, "ENABLE_RERANKER", False):
        reranker = get_reranker()
        assert isinstance(reranker, NoOpProvider)


def test_get_reranker_enabled_with_key():
    with patch.object(settings, "ENABLE_RERANKER", True), \
         patch.object(settings, "JINA_API_KEY", "jina_test_key"):
        reranker = get_reranker()
        assert isinstance(reranker, JinaRerankProvider)
        assert reranker.api_key == "jina_test_key"


def test_disabled_reranker_makes_zero_http_calls(sample_candidates):
    """
    Assert that when ENABLE_RERANKER is False, reranking makes ZERO HTTP requests.
    Guarantees no false-green test.
    """
    with patch.object(settings, "ENABLE_RERANKER", False), \
         patch("httpx.Client.post") as mock_post:
        reranker = get_reranker()
        result = reranker.rerank("query tìm kiếm", sample_candidates, top_n=3)

        # Assert no HTTP calls to Jina
        mock_post.assert_not_called()
        assert len(result) == 3
        assert [c["chunk"].id for c in result] == [1, 2, 3]

