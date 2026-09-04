import hashlib
import logging
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import delete, select
import pypdfium2 as pdfium

from app.core.config import settings
from app.core.observability import observe_llm, update_trace_context
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.enums import AssetIngestionStatus
from app.services.storage_service import download_object
from app.rag.ingestion.embeddings import (
    _EMBEDDING_SEMAPHORE,
    EmbeddingRateLimiter,
    _embedding_rate_limiter,
    get_genai_client,
    _is_retryable_gemini_error,
    _is_retryable_embedding_error,
    _embed_batch_with_retry,
    EmbeddingProvider,
    GeminiEmbeddingProvider,
    JinaEmbeddingProvider,
    get_embedding_provider,
)
from app.rag.ingestion.splitter import (
    _chunking_context,
    safe_sent_tokenize,
    get_sentence_splitter,
    chunk_text_by_words,
)

logger = logging.getLogger(__name__)


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


@observe_llm(name="document_ingestion")
def ingest_asset(asset_id: int, db: Session) -> bool:
    """
    Main ingestion workflow for an asset (extraction, chunking, embedding, db save).
    """
    # 1. Fetch asset
    asset = db.get(Asset, asset_id)
    if not asset:
        logger.error(f"Asset {asset_id} not found.")
        return False

    update_trace_context(
        tags=["ingestion", f"asset-{asset_id}"],
        asset_id=asset_id,
        file_name=asset.file_name,
        file_path=asset.file_path,
    )

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
                    chunk_index=old_emb.chunk_index,
                    content=old_emb.content,
                    embedding=old_emb.embedding,
                    page_number=old_emb.page_number,
                    token_count=old_emb.token_count,
                    metadata_={},
                )
                for old_emb in existing_embeddings
            ]
            db.add_all(new_embeddings)

            asset.ingestion_status = AssetIngestionStatus.COMPLETED
            asset.chunk_count = len(new_embeddings)
            asset.ingestion_error = None
            db.commit()
            logger.info(
                f"Deduplication completed successfully for asset {asset_id}: cloned {len(new_embeddings)} chunks without calling Gemini API."
            )
            update_trace_context(
                dedup_hit=True,
                cloned_from_asset_id=existing_asset.id,
                chunk_count=len(new_embeddings),
            )
            return True

        # 7. Extract text with streaming generator and page-aware chunking (Sentence-Aware)
        logger.info(f"Extracting PDF pages with streaming generator for asset {asset_id}")
        total_chars = 0
        chunk_index = 0
        chunks_info = []

        splitter = get_sentence_splitter()
        for page_num, page_text in extract_pdf_pages_stream(file_data):
            total_chars += len(page_text)
            if not page_text:
                continue

            ctx_token = _chunking_context.set((asset_id, page_num))
            try:
                page_chunks = splitter.split_text(page_text)
            finally:
                _chunking_context.reset(ctx_token)

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
        if total_chars < settings.INGESTION_MIN_PDF_CHAR_THRESHOLD:
            asset.ingestion_status = AssetIngestionStatus.FAILED
            asset.ingestion_error = "SCANNED_DOCUMENT_UNSUPPORTED"
            db.commit()
            logger.warning(
                f"Asset {asset_id} ingestion failed: total characters {total_chars} < {settings.INGESTION_MIN_PDF_CHAR_THRESHOLD}."
            )
            update_trace_context(
                scanned_guard_failed=True,
                total_chars=total_chars,
            )
            return False

        if not chunks_info:
            raise ValueError("No text chunks were generated from the document.")

        # 9. Batch Call Embedding API based on Token Budget
        logger.info(f"Generating embeddings for {len(chunks_info)} chunks in token-budgeted batches")
        embedding_provider = get_embedding_provider()

        tpm_budget = settings.ACTIVE_EMBEDDING_TPM_BUDGET_PER_BATCH
        max_chunks_cap = settings.ACTIVE_EMBEDDING_MAX_CHUNKS_PER_BATCH

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
                    embedding_provider,
                    batch_data["contents"],
                    estimated_tokens=batch_data["estimated_tokens"],
                )
                all_embeddings.extend(batch_embeddings)

        if len(all_embeddings) != len(chunks_info):
            raise RuntimeError(f"Embedding count mismatch: expected {len(chunks_info)}, got {len(all_embeddings)}")

        for idx, emb_val in enumerate(all_embeddings):
            chunks_info[idx]["embedding"] = emb_val

        # 10. Save new embeddings to DB
        total_chunks = len(chunks_info)
        for chunk in chunks_info:
            idx = chunk["chunk_index"]
            chunk_metadata = {
                "node_id": f"asset_{asset_id}_chunk_{idx}",
                "prev_chunk_index": idx - 1 if idx > 0 else None,
                "next_chunk_index": idx + 1 if idx < total_chunks - 1 else None,
            }
            asset_emb = AssetEmbedding(
                asset_id=asset_id,
                chunk_index=idx,
                content=chunk["content"],
                embedding=chunk["embedding"],
                page_number=chunk["page_number"],
                token_count=chunk["token_count"],
                metadata_=chunk_metadata,
            )
            db.add(asset_emb)

        # 11. Final update to asset status
        asset.ingestion_status = AssetIngestionStatus.COMPLETED
        asset.chunk_count = len(chunks_info)
        asset.ingestion_error = None
        db.commit()
        logger.info(f"Ingestion completed successfully for asset {asset_id} with {len(chunks_info)} chunks.")
        update_trace_context(
            dedup_hit=False,
            total_chars=total_chars,
            chunk_count=len(chunks_info),
            total_batches=len(batches),
        )
        return True

    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error during ingestion for asset {asset_id}")
        update_trace_context(error=str(e))
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


__all__ = [
    "_EMBEDDING_SEMAPHORE",
    "EmbeddingRateLimiter",
    "_embedding_rate_limiter",
    "get_genai_client",
    "_is_retryable_gemini_error",
    "_is_retryable_embedding_error",
    "_embed_batch_with_retry",
    "_chunking_context",
    "safe_sent_tokenize",
    "get_sentence_splitter",
    "chunk_text_by_words",
    "extract_pdf_pages_stream",
    "ingest_asset",
    "ingest_asset_background_task",
    "download_object",
]
