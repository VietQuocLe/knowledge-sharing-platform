import hashlib
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Set environment overrides
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("MINIO_HOST", "localhost")

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.enums import AssetIngestionStatus
from app.models.notebook import Notebook
from app.models.user import User
from app.services.ingestion_service import extract_pdf_pages_stream, ingest_asset


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_pdf_bytes():
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument.new()
    # Create page with enough text for normal test
    page = doc.new_page(width=595, height=842)
    # We can save empty or raw document
    import io
    buf = io.BytesIO()
    doc.save(buf)
    page.close()
    doc.close()
    return buf.getvalue()


def test_extract_pdf_pages_stream(sample_pdf_bytes):
    pages = list(extract_pdf_pages_stream(sample_pdf_bytes))
    assert len(pages) == 1
    assert pages[0][0] == 1  # Page number 1


def test_ingestion_and_deduplication(db_session):
    # 0. Setup test user and notebook
    user = User(email="dedup_test_user@example.com", password_hash="hashed_pw", full_name="Dedup User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    notebook = Notebook(title="Dedup Notebook", owner_id=user.id)
    db_session.add(notebook)
    db_session.commit()
    db_session.refresh(notebook)

    try:
        # Create fake text and bytes
        fake_pdf_content = b"%PDF-1.4 Mock PDF Content For Ingestion Test " + b"word " * 100
        computed_hash = hashlib.sha256(fake_pdf_content).hexdigest()

        # 1. Create Asset 1
        asset_1 = Asset(
            notebook_id=notebook.id,
            file_name="doc_1.pdf",
            file_path="notebooks/1/doc_1.pdf",
            file_type="application/pdf",
            size=len(fake_pdf_content),
            ingestion_status=AssetIngestionStatus.PENDING,
        )
        db_session.add(asset_1)
        db_session.commit()
        db_session.refresh(asset_1)

        # Mock download_object and extract_pdf_pages_stream, and embedding batch
        mock_pages = [(1, "Knowledge sharing platform is a great educational project " * 10)]
        fake_embedding = [0.1] * 768

        with patch("app.services.ingestion_service.download_object", return_value=fake_pdf_content), \
             patch("app.services.ingestion_service.extract_pdf_pages_stream", return_value=mock_pages), \
             patch("app.services.ingestion_service._embed_batch_with_retry", return_value=[fake_embedding]) as mock_embed:

            # Ingest Asset 1 (First Time - Full Embedding)
            success_1 = ingest_asset(asset_1.id, db_session)
            assert success_1 is True
            assert mock_embed.call_count >= 1

            db_session.refresh(asset_1)
            assert asset_1.ingestion_status == AssetIngestionStatus.COMPLETED
            assert asset_1.file_hash == computed_hash
            assert asset_1.chunk_count >= 1

            embeddings_1 = db_session.query(AssetEmbedding).filter(AssetEmbedding.asset_id == asset_1.id).all()
            assert len(embeddings_1) == asset_1.chunk_count

        # 2. Create Asset 2 with SAME content (should trigger deduplication)
        asset_2 = Asset(
            notebook_id=notebook.id,
            file_name="doc_2.pdf",
            file_path="notebooks/1/doc_2.pdf",
            file_type="application/pdf",
            size=len(fake_pdf_content),
            ingestion_status=AssetIngestionStatus.PENDING,
        )
        db_session.add(asset_2)
        db_session.commit()
        db_session.refresh(asset_2)

        with patch("app.services.ingestion_service.download_object", return_value=fake_pdf_content), \
             patch("app.services.ingestion_service._embed_batch_with_retry") as mock_embed_2:

            # Ingest Asset 2 (Deduplication - Should NOT call embedding API)
            success_2 = ingest_asset(asset_2.id, db_session)
            assert success_2 is True
            # Verified: NO embedding API call was made!
            mock_embed_2.assert_not_called()

            db_session.refresh(asset_2)
            assert asset_2.ingestion_status == AssetIngestionStatus.COMPLETED
            assert asset_2.file_hash == computed_hash
            assert asset_2.chunk_count == asset_1.chunk_count

            # Verify cloned embeddings exist and have distinct IDs
            embeddings_2 = db_session.query(AssetEmbedding).filter(AssetEmbedding.asset_id == asset_2.id).all()
            assert len(embeddings_2) == len(embeddings_1)
            for e1, e2 in zip(embeddings_1, embeddings_2):
                assert e1.id != e2.id  # Distinct DB primary keys
                assert e2.asset_id == asset_2.id
                assert e1.chunk_index == e2.chunk_index
                assert e1.content == e2.content
                assert e1.page_number == e2.page_number

    finally:
        # Cleanup
        db_session.delete(user)
        db_session.commit()

