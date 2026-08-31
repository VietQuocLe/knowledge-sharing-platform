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
from app.models.enums import AssetConversionStatus, AssetIngestionStatus
from app.models.notebook import Notebook
from app.models.user import User
from app.services.conversion_service import (
    _convert_via_cloudmersive,
    convert_docx_to_pdf_task,
)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_convert_via_cloudmersive_no_key():
    with patch("app.core.config.settings.CLOUDMERSIVE_API_KEY", None):
        with pytest.raises(ValueError, match="CLOUDMERSIVE_API_KEY is not configured"):
            _convert_via_cloudmersive(b"fake docx", "sample.docx")


def test_convert_via_cloudmersive_success():
    fake_pdf = b"%PDF-1.4 Mock Converted PDF bytes"
    mock_res = MagicMock()
    mock_res.content = fake_pdf
    mock_res.raise_for_status = MagicMock()

    with patch("app.core.config.settings.CLOUDMERSIVE_API_KEY", "test-api-key"), \
         patch("httpx.Client.post", return_value=mock_res) as mock_post:
        pdf_bytes = _convert_via_cloudmersive(b"fake docx", "sample.docx")
        assert pdf_bytes == fake_pdf
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["Apikey"] == "test-api-key"
        assert "inputFile" in kwargs["files"]


def test_convert_docx_dual_mode_cloudmersive_priority(db_session):
    user = User(email="conv_user@example.com", password_hash="hashed_pw", full_name="Conv User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    notebook = Notebook(title="Conv Notebook", owner_id=user.id)
    db_session.add(notebook)
    db_session.commit()
    db_session.refresh(notebook)

    asset = Asset(
        notebook_id=notebook.id,
        file_name="sample.docx",
        file_path="notebooks/1/sample.docx",
        file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size=100,
        conversion_status=AssetConversionStatus.PENDING,
        ingestion_status=AssetIngestionStatus.PENDING,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    fake_pdf = b"%PDF-1.4 Mock Converted PDF bytes"

    try:
        # Mock MinIO get_object
        mock_minio_resp = MagicMock()
        mock_minio_resp.read.return_value = b"fake docx content"
        mock_minio_client = MagicMock()
        mock_minio_client.get_object.return_value = mock_minio_resp

        with patch("app.services.conversion_service.get_minio_client", return_value=mock_minio_client), \
             patch("app.core.config.settings.CLOUDMERSIVE_API_KEY", "valid-key"), \
             patch("app.services.conversion_service._convert_via_cloudmersive", return_value=fake_pdf) as mock_cloud, \
             patch("app.services.conversion_service._convert_via_local_soffice") as mock_soffice, \
             patch("app.services.storage_service.upload_object") as mock_upload, \
             patch("app.services.ingestion_service.ingest_asset") as mock_ingest:

            convert_docx_to_pdf_task(asset.id)

            mock_cloud.assert_called_once()
            mock_soffice.assert_not_called()
            mock_upload.assert_called_once()
            mock_ingest.assert_called_once()

            db_session.refresh(asset)
            assert asset.conversion_status == AssetConversionStatus.COMPLETED
            assert asset.converted_pdf_path == f"derived/{asset.id}.pdf"

    finally:
        db_session.delete(user)
        db_session.commit()


def test_convert_docx_fallback_to_local_when_cloudmersive_fails(db_session):
    user = User(email="conv_fallback_user@example.com", password_hash="hashed_pw", full_name="Fallback User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    notebook = Notebook(title="Fallback Notebook", owner_id=user.id)
    db_session.add(notebook)
    db_session.commit()
    db_session.refresh(notebook)

    asset = Asset(
        notebook_id=notebook.id,
        file_name="fallback.docx",
        file_path="notebooks/1/fallback.docx",
        file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size=100,
        conversion_status=AssetConversionStatus.PENDING,
        ingestion_status=AssetIngestionStatus.PENDING,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    fake_pdf = b"%PDF-1.4 Mock Local PDF bytes"

    try:
        mock_minio_resp = MagicMock()
        mock_minio_resp.read.return_value = b"fake docx content"
        mock_minio_client = MagicMock()
        mock_minio_client.get_object.return_value = mock_minio_resp

        with patch("app.services.conversion_service.get_minio_client", return_value=mock_minio_client), \
             patch("app.core.config.settings.CLOUDMERSIVE_API_KEY", "valid-key"), \
             patch("app.services.conversion_service._convert_via_cloudmersive", side_effect=Exception("API limit exceeded")) as mock_cloud, \
             patch("app.services.conversion_service._convert_via_local_soffice", return_value=fake_pdf) as mock_soffice, \
             patch("app.services.storage_service.upload_object") as mock_upload, \
             patch("app.services.ingestion_service.ingest_asset") as mock_ingest:

            convert_docx_to_pdf_task(asset.id)

            mock_cloud.assert_called_once()
            mock_soffice.assert_called_once()
            mock_upload.assert_called_once()
            mock_ingest.assert_called_once()

            db_session.refresh(asset)
            assert asset.conversion_status == AssetConversionStatus.COMPLETED
            assert asset.converted_pdf_path == f"derived/{asset.id}.pdf"

    finally:
        db_session.delete(user)
        db_session.commit()


def test_convert_docx_failure_sets_failed_status(db_session):
    user = User(email="conv_fail_user@example.com", password_hash="hashed_pw", full_name="Fail User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    notebook = Notebook(title="Fail Notebook", owner_id=user.id)
    db_session.add(notebook)
    db_session.commit()
    db_session.refresh(notebook)

    asset = Asset(
        notebook_id=notebook.id,
        file_name="fail.docx",
        file_path="notebooks/1/fail.docx",
        file_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size=100,
        conversion_status=AssetConversionStatus.PENDING,
        ingestion_status=AssetIngestionStatus.PENDING,
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    try:
        mock_minio_resp = MagicMock()
        mock_minio_resp.read.return_value = b"fake docx content"
        mock_minio_client = MagicMock()
        mock_minio_client.get_object.return_value = mock_minio_resp

        with patch("app.services.conversion_service.get_minio_client", return_value=mock_minio_client), \
             patch("app.core.config.settings.CLOUDMERSIVE_API_KEY", None), \
             patch("app.services.conversion_service._convert_via_local_soffice", side_effect=Exception("soffice crash")):

            convert_docx_to_pdf_task(asset.id)

            db_session.refresh(asset)
            assert asset.conversion_status == AssetConversionStatus.FAILED
            assert asset.ingestion_status == AssetIngestionStatus.FAILED
            assert asset.ingestion_error == "CONVERSION_FAILED"

    finally:
        db_session.delete(user)
        db_session.commit()

