import hashlib
import logging
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import delete
import pypdfium2 as pdfium
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.enums import AssetIngestionStatus
from app.services.storage_service import download_object

logger = logging.getLogger(__name__)


def get_genai_client() -> genai.Client:
    """
    Initializes Google GenAI Client with settings.GOOGLE_API_KEY.
    """
    return genai.Client(api_key=settings.GOOGLE_API_KEY)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def _embed_batch_with_retry(client: genai.Client, contents: list[str]) -> list[list[float]]:
    """
    Calls Gemini embedding service with exponential backoff retry.
    """
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

        # 6. Extract text with pypdfium2
        logger.info(f"Extracting PDF pages for asset {asset_id}")
        pages_text = []
        with pdfium.PdfDocument(file_data) as doc:
            for i in range(len(doc)):
                page = doc[i]
                textpage = page.get_textpage()
                text = textpage.get_text_range()
                text_cleaned = (text or "").strip()
                pages_text.append((i + 1, text_cleaned))

        # 7. Scanned Guard check
        total_chars = sum(len(text) for _, text in pages_text)
        if total_chars < 100:
            asset.ingestion_status = AssetIngestionStatus.FAILED
            asset.ingestion_error = "SCANNED_DOCUMENT_UNSUPPORTED"
            db.commit()
            logger.warning(f"Asset {asset_id} ingestion failed: total characters {total_chars} < 100.")
            return False

        # 8. Page-aware chunking
        chunk_index = 0
        chunks_info = []
        for page_num, page_text in pages_text:
            if not page_text:
                continue
            page_chunks = chunk_text_by_words(page_text, chunk_size_words=600, overlap_words=100)
            for chunk_txt in page_chunks:
                chunks_info.append({
                    "chunk_index": chunk_index,
                    "page_number": page_num,
                    "content": chunk_txt
                })
                chunk_index += 1

        if not chunks_info:
            raise ValueError("No text chunks were generated from the document.")

        # 9. Batch Call Gemini Embedding API
        logger.info(f"Generating embeddings for {len(chunks_info)} chunks in batches")
        client = get_genai_client()
        batch_size = 15

        contents = [c["content"] for c in chunks_info]
        all_embeddings = []

        for idx in range(0, len(contents), batch_size):
            batch = contents[idx : idx + batch_size]
            batch_embeddings = _embed_batch_with_retry(client, batch)
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
        asset.ingestion_status = AssetIngestionStatus.FAILED
        asset.ingestion_error = str(e)
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

