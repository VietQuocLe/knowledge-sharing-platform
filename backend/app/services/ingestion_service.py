"""
Proxy re-export module for backward compatibility.
Original implementation has been migrated to app.rag.ingestion.pipeline.
"""
from app.rag.ingestion.pipeline import (
    _EMBEDDING_SEMAPHORE,
    EmbeddingRateLimiter,
    _embedding_rate_limiter,
    get_genai_client,
    _is_retryable_gemini_error,
    _embed_batch_with_retry,
    chunk_text_by_words,
    extract_pdf_pages_stream,
    ingest_asset,
    ingest_asset_background_task,
    download_object,
)
from app.rag.ingestion.pipeline import *  # noqa: F401, F403
