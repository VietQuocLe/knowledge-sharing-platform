import contextvars
from functools import lru_cache
import logging
import re

from llama_index.core.node_parser import SentenceSplitter
import underthesea

from app.core.config import settings

logger = logging.getLogger(__name__)

# Context variable to hold (asset_id, page_number) for safe logging inside sentence tokenizer
_chunking_context: contextvars.ContextVar[tuple[int | None, int | None]] = contextvars.ContextVar(
    "_chunking_context", default=(None, None)
)


def safe_sent_tokenize(text: str) -> list[str]:
    """
    Safely tokenizes sentences in Vietnamese using underthesea.sent_tokenize.
    If underthesea encounters abnormal text/errors (e.g. ASCII tables, corrupted Unicode),
    logs a warning with (asset_id, page_number) context and falls back to regex sentence splitting.
    """
    try:
        return underthesea.sent_tokenize(text)
    except Exception as exc:
        asset_id, page_number = _chunking_context.get()
        logger.warning(
            "underthesea sent_tokenize failed for asset_id=%s page=%s, falling back to regex splitter: %s",
            asset_id,
            page_number,
            exc,
        )
        chunks = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        return chunks if chunks else [text]


@lru_cache(maxsize=1)
def get_sentence_splitter() -> SentenceSplitter:
    """
    Returns a cached singleton instance of LlamaIndex SentenceSplitter
    configured with chunk_size=600, chunk_overlap=100, and safe_sent_tokenize.
    """
    try:
        return SentenceSplitter(
            chunk_size=600,
            chunk_overlap=100,
            chunking_tokenizer_fn=safe_sent_tokenize,
        )
    except TypeError:
        # Fallback for older LlamaIndex variants where the parameter was named sentence_splitter
        return SentenceSplitter(
            chunk_size=600,
            chunk_overlap=100,
            sentence_splitter=safe_sent_tokenize,
        )


def chunk_text_by_words(
    text: str,
    chunk_size_words: int | None = None,
    overlap_words: int | None = None,
) -> list[str]:
    """
    (Deprecated) Splits text into chunks of specified word count with word overlap.
    Retained for backward compatibility.
    """
    if chunk_size_words is None:
        chunk_size_words = settings.INGESTION_CHUNK_SIZE_WORDS
    if overlap_words is None:
        overlap_words = settings.INGESTION_CHUNK_OVERLAP_WORDS

    words = text.split()
    if not words:
        return []

    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size_words]
        chunks.append(" ".join(chunk_words))

        if i + chunk_size_words >= len(words):
            break
        i += chunk_size_words - overlap_words

    return chunks


__all__ = [
    "_chunking_context",
    "safe_sent_tokenize",
    "get_sentence_splitter",
    "chunk_text_by_words",
]

