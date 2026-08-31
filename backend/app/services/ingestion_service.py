import hashlib
import logging
import threading
import time
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import delete
import pypdfium2 as pdfium
from google import genai
from google.genai import errors, types
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.enums import AssetIngestionStatus
from app.services.storage_service import download_object

logger = logging.getLogger(__name__)

# Task 0: Global semaphore to serialize all Gemini Embedding API calls (single-thread)
_EMBEDDING_SEMAPHORE = threading.Semaphore(1)


class EmbeddingRateLimiter:
    """
    Sliding-window (60s) rate and token limiter for Gemini Embedding API.
    Tracks both (a) request count (RPM) and (b) token consumption (TPM) in a 60-second window.
    """

    def __init__(self, window_seconds: float = 60.0):
        self.window_seconds = window_seconds
        self._history: list[tuple[float, int]] = []  # List of (timestamp, token_count)
        self._lock = threading.Lock()

    def acquire(self, estimated_tokens: int) -> None:
        """
        Blocks until capacity (RPM and TPM) is available within the sliding window,
        then records the new request and token allocation.
        """
        rpm_limit = getattr(settings, "GEMINI_EMBEDDING_RPM_LIMIT", 80)
        tpm_limit = getattr(settings, "GEMINI_EMBEDDING_TPM_LIMIT", 26000)

        while True:
            with self._lock:
                now = time.time()
                cutoff = now - self.window_seconds

                # Clean up entries older than 60s
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


def _is_retryable_gemini_error(exception: BaseException) -> bool:
    """
    Identifies retryable exceptions for Gemini Embedding calls:
    - 429 ClientError (Rate limit / Resource exhausted)
    - 5xx ServerError (500 Internal, 503 Unavailable, 504 Gateway Timeout)
    - Network / Connection / Timeout exceptions
    All other exceptions (400 Bad Request, 401 Auth, 403 Forbidden, 404, etc.) are non-retryable.
    """
    if isinstance(exception, errors.APIError):
        if exception.code == 429 or (exception.code and 500 <= exception.code < 600):
            return True
        return False
    if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError, TimeoutError, ConnectionError)):
        return True
    return False


@retry(
    retry=retry_if_exception(_is_retryable_gemini_error),
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    reraise=True
)
def _embed_batch_with_retry(
    client: genai.Client,
    contents: list[str],
    estimated_tokens: int = 0
) -> list[list[float]]:
    """
    Calls Gemini embedding service with exponential backoff retry for transient/rate-limit errors.
    Acquires rate limiter capacity immediately before sending the API request.
    """
    if estimated_tokens <= 0:
        estimated_tokens = sum(max(1, int(len(c.split()) * 1.3)) for c in contents)

    _embedding_rate_limiter.acquire(estimated_tokens)

    response = client.models.embed_content(
        model=settings.GEMINI_EMBEDDING_MODEL,
        contents=contents,
        config=types.EmbedContentConfig(
            output_dimensionality=settings.EMBEDDING_DIMENSION,
            task_type="RETRIEVAL_DOCUMENT",
        )
    )
    return [emb.values for emb in response.embeddings]


def chunk_text_by_words(text: str, chunk_size_words: int = 600, overlap_words: int = 100) -> list[str]:
    """
    Splits text into chunks of specified word count with word overlap.
    """
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


def extract_pdf_pages_stream(file_data: bytes):
    """
    Streams PDF page numbers and text page-by-page while immediately closing
    both textpage and page C-layer structures to maintain flat memory usage (<30MB).
    """
    with pdfium.PdfDocument(file_data) as doc:
        for i in range(len(doc)):
            page = doc[i]
            try:
                textpage = page.get_textpage()
                try:
                    text = textpage.get_text_range()
                    text_cleaned = (text or "").strip()
                    yield i + 1, text_cleaned
                finally:
                    textpage.close()
            finally:
                page.close()


def ingest_asset(asset_id: int, db: Session) -> bool:
    """
    Main ingestion workflow for an asset (extraction, chunking, embedding, db save).
    """
    # 1. Fetch asset
    asset = db.get(Asset, asset_id)
    if not asset:
        logger.error(f"Asset {asset_id} not found.")
        return False

    # 2. Update status to PROCESSING, reset chunk count, and delete old embeddings (Idempotency check)
    asset.ingestion_status = AssetIngestionStatus.PROCESSING
    asset.chunk_count = 0
    db.execute(delete(AssetEmbedding).where(AssetEmbedding.asset_id == asset_id))
    db.commit()

    try:
        # 3. Determine file path (prefer converted_pdf_path)
        file_path = asset.converted_pdf_path if asset.converted_pdf_path else asset.file_path
        if not file_path:
            raise ValueError("No file path available for download.")

        # 4. Download file from MinIO
        logger.info(f"Downloading asset {asset_id} from path {file_path}")
        file_data = download_object(file_path)

        # 5. Compute SHA-256 and update
        file_hash = hashlib.sha256(file_data).hexdigest()
        asset.file_hash = file_hash
        db.commit()

        # 6. Check for content-addressable deduplication (reusing embeddings from existing completed asset)
        from sqlalchemy import select
        existing_asset = db.execute(
            select(Asset).where(
                Asset.file_hash == file_hash,
                Asset.ingestion_status == AssetIngestionStatus.COMPLETED,
                Asset.id != asset_id,
            )
        ).scalars().first()

        if existing_asset:
            logger.info(
                f"Asset {asset_id} matched existing completed asset {existing_asset.id} with hash {file_hash}. Reusing embeddings."
            )
            existing_embeddings = db.execute(
                select(AssetEmbedding)
                .where(AssetEmbedding.asset_id == existing_asset.id)
                .order_by(AssetEmbedding.chunk_index.asc())
            ).scalars().all()

            new_embeddings = [
                AssetEmbedding(
                    asset_id=asset_id,
                    chunk_index=emb.chunk_index,
                    content=emb.content,
                    embedding=emb.embedding,
                    page_number=emb.page_number,
                    token_count=emb.token_count,
                    metadata_=dict(emb.metadata_) if emb.metadata_ else {},
                )
                for emb in existing_embeddings
            ]
            db.add_all(new_embeddings)

            asset.ingestion_status = AssetIngestionStatus.COMPLETED
            asset.chunk_count = len(new_embeddings)
            asset.ingestion_error = None
            db.commit()
            logger.info(
                f"Deduplication completed successfully for asset {asset_id}: cloned {len(new_embeddings)} chunks without calling Gemini API."
            )
            return True

        # 7. Extract text with streaming generator and page-aware chunking
        logger.info(f"Extracting PDF pages with streaming generator for asset {asset_id}")
        total_chars = 0
        chunk_index = 0
        chunks_info = []

        for page_num, page_text in extract_pdf_pages_stream(file_data):
            total_chars += len(page_text)
            if not page_text:
                continue
            page_chunks = chunk_text_by_words(page_text, chunk_size_words=600, overlap_words=100)
            for chunk_txt in page_chunks:
                words = chunk_txt.split()
                token_count = max(1, int(len(words) * 1.3))
                chunks_info.append({
                    "chunk_index": chunk_index,
                    "page_number": page_num,
                    "content": chunk_txt,
                    "token_count": token_count,
                })
                chunk_index += 1

        # 8. Scanned Guard check
        if total_chars < 100:
            asset.ingestion_status = AssetIngestionStatus.FAILED
            asset.ingestion_error = "SCANNED_DOCUMENT_UNSUPPORTED"
            db.commit()
            logger.warning(f"Asset {asset_id} ingestion failed: total characters {total_chars} < 100.")
            return False

        if not chunks_info:
            raise ValueError("No text chunks were generated from the document.")

        # 9. Batch Call Gemini Embedding API based on Token Budget
        logger.info(f"Generating embeddings for {len(chunks_info)} chunks in token-budgeted batches")
        client = get_genai_client()

        tpm_budget = getattr(settings, "GEMINI_EMBEDDING_TPM_BUDGET_PER_BATCH", 24000)
        max_chunks_cap = getattr(settings, "GEMINI_EMBEDDING_MAX_CHUNKS_PER_BATCH", 80)

        batches: list[dict[str, Any]] = []
        current_batch_chunks: list[dict[str, Any]] = []
        current_batch_tokens = 0

        for chunk in chunks_info:
            token_count = chunk["token_count"]
            # Cut to next batch if adding this chunk exceeds token budget (and current batch non-empty) or hits max chunks
            if current_batch_chunks and (
                current_batch_tokens + token_count > tpm_budget
                or len(current_batch_chunks) >= max_chunks_cap
            ):
                batches.append({
                    "contents": [c["content"] for c in current_batch_chunks],
                    "estimated_tokens": current_batch_tokens,
                })
                current_batch_chunks = []
                current_batch_tokens = 0

            current_batch_chunks.append(chunk)
            current_batch_tokens += token_count

        if current_batch_chunks:
            batches.append({
                "contents": [c["content"] for c in current_batch_chunks],
                "estimated_tokens": current_batch_tokens,
            })

        all_embeddings = []
        with _EMBEDDING_SEMAPHORE:
            for batch_idx, batch_data in enumerate(batches, start=1):
                logger.info(
                    f"Processing embedding batch {batch_idx}/{len(batches)} "
                    f"({len(batch_data['contents'])} chunks, ~{batch_data['estimated_tokens']} tokens)"
                )
                batch_embeddings = _embed_batch_with_retry(
                    client,
                    batch_data["contents"],
                    estimated_tokens=batch_data["estimated_tokens"],
                )
                all_embeddings.extend(batch_embeddings)

        if len(all_embeddings) != len(chunks_info):
            raise RuntimeError(f"Embedding count mismatch: expected {len(chunks_info)}, got {len(all_embeddings)}")

        for idx, emb_val in enumerate(all_embeddings):
            chunks_info[idx]["embedding"] = emb_val

        # 10. Save new embeddings to DB
        for chunk in chunks_info:
            asset_emb = AssetEmbedding(
                asset_id=asset_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                embedding=chunk["embedding"],
                page_number=chunk["page_number"],
                token_count=chunk["token_count"],
                metadata_={}
            )
            db.add(asset_emb)

        # 11. Final update to asset status
        asset.ingestion_status = AssetIngestionStatus.COMPLETED
        asset.chunk_count = len(chunks_info)
        asset.ingestion_error = None
        db.commit()
        logger.info(f"Ingestion completed successfully for asset {asset_id} with {len(chunks_info)} chunks.")
        return True

    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error during ingestion for asset {asset_id}")
        # Re-fetch local asset record from DB since the previous instance was expired by rollback
        asset_record = db.get(Asset, asset_id)
        if asset_record:
            asset_record.ingestion_status = AssetIngestionStatus.FAILED
            asset_record.ingestion_error = str(e)
            db.commit()
        return False


def ingest_asset_background_task(asset_id: int) -> None:
    """
    Background task wrapper to run ingest_asset with an independent database session.
    """
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        logger.info(f"Triggering background ingestion for asset {asset_id}")
        ingest_asset(asset_id, db)
    except Exception as e:
        logger.exception(f"Unexpected error in background ingestion for asset {asset_id}")
    finally:
        db.close()

