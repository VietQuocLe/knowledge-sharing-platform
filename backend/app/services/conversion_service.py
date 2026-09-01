import logging
import os
import subprocess
import tempfile
import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.enums import AssetConversionStatus, AssetIngestionStatus
from app.services import storage_service
from app.services.storage_service import get_minio_client

logger = logging.getLogger(__name__)


def _convert_via_cloudmersive(docx_bytes: bytes, filename: str) -> bytes:
    """
    Converts a DOCX file to PDF using Cloudmersive Document Conversion REST API.
    """
    if not settings.CLOUDMERSIVE_API_KEY:
        raise ValueError("CLOUDMERSIVE_API_KEY is not configured.")

    url = "https://api.cloudmersive.com/convert/docx/to/pdf"
    headers = {
        "Apikey": settings.CLOUDMERSIVE_API_KEY,
    }
    files = {
        "inputFile": (filename, docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    }

    logger.info(f"Calling Cloudmersive API to convert '{filename}' ({len(docx_bytes)} bytes)...")
    with httpx.Client(timeout=settings.CLOUDMERSIVE_TIMEOUT_SECONDS) as client:
        response = client.post(url, headers=headers, files=files)
        response.raise_for_status()
        pdf_bytes = response.content

    if not pdf_bytes or len(pdf_bytes) < 10:
        raise ValueError("Cloudmersive returned empty or invalid PDF response.")

    logger.info(f"Cloudmersive conversion succeeded ({len(pdf_bytes)} bytes generated).")
    return pdf_bytes


def _convert_via_local_soffice(docx_bytes: bytes) -> bytes:
    """
    Fallback: Converts a DOCX file to PDF using local LibreOffice/soffice process.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_docx_path = os.path.join(tmpdir, "input.docx")
        with open(input_docx_path, "wb") as f:
            f.write(docx_bytes)

        # Create distinct user profile directory inside temp dir to prevent concurrency profile lock errors
        user_profile_dir = os.path.join(tmpdir, "libreoffice_profile")
        os.makedirs(user_profile_dir, exist_ok=True)

        # Format the profile path into a file URL compatible with LibreOffice
        path_str = user_profile_dir.replace(os.sep, '/')
        if not path_str.startswith('/'):
            path_str = '/' + path_str
        user_profile_url = f"file://{path_str}"

        cmd = [
            "soffice",
            "--headless",
            "--norestore",
            f"-env:UserInstallation={user_profile_url}",
            "--convert-to",
            "pdf",
            "--outdir",
            tmpdir,
            input_docx_path,
        ]

        logger.info(f"Running local LibreOffice conversion cmd: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=settings.LIBREOFFICE_TIMEOUT_SECONDS,
            check=True,
        )
        logger.info(f"LibreOffice stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"LibreOffice stderr: {result.stderr}")

        expected_pdf_path = os.path.join(tmpdir, "input.pdf")
        if not os.path.exists(expected_pdf_path):
            raise FileNotFoundError(f"Conversion command ran but output PDF not found at {expected_pdf_path}")

        with open(expected_pdf_path, "rb") as f:
            return f.read()


def convert_docx_to_pdf_task(asset_id: int) -> None:
    """
    Background task to download a DOCX file from MinIO, convert it to PDF
    (preferring Cloudmersive API when key is configured, with local soffice fallback),
    and upload the converted PDF back to MinIO.
    """
    logger.info(f"Starting background conversion task for asset ID: {asset_id}")
    db = SessionLocal()
    try:
        # Retrieve asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            logger.error(f"Asset with ID {asset_id} not found for conversion.")
            return

        # Double check conversion status and type
        if asset.file_type != "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            logger.warning(f"Asset {asset_id} file type is not DOCX. Skipping conversion. file_type: {asset.file_type}")
            return

        # 1. Download original DOCX file from MinIO
        try:
            client = get_minio_client()
            response = client.get_object(settings.MINIO_BUCKET_NAME, asset.file_path)
            docx_data = response.read()
            response.close()
            response.release_conn()
        except Exception as e:
            logger.exception(f"Failed to download asset {asset_id} from path {asset.file_path}: {e}")
            asset.conversion_status = AssetConversionStatus.FAILED
            db.commit()
            return

        # 2. Dual-mode conversion execution
        pdf_data = None

        # Mode A: Cloudmersive API (if API Key is configured)
        if settings.CLOUDMERSIVE_API_KEY:
            try:
                pdf_data = _convert_via_cloudmersive(docx_data, asset.file_name)
            except Exception as e:
                logger.warning(f"Cloudmersive conversion failed for asset {asset_id}: {e}. Falling back to local soffice.")
                pdf_data = None

        # Mode B: Local LibreOffice fallback (if Cloudmersive not configured or failed)
        if pdf_data is None:
            try:
                pdf_data = _convert_via_local_soffice(docx_data)
            except Exception as e:
                logger.error(f"Local soffice conversion failed for asset {asset_id}: {e}")
                asset.conversion_status = AssetConversionStatus.FAILED
                db.commit()
                return

        # 3. Upload converted PDF to MinIO
        derived_key = f"derived/{asset.id}.pdf"
        try:
            storage_service.upload_object(
                object_path=derived_key,
                data=pdf_data,
                content_type="application/pdf",
            )
        except Exception as e:
            logger.error(f"Failed to upload converted PDF of asset {asset_id} to MinIO key {derived_key}: {e}")
            asset.conversion_status = AssetConversionStatus.FAILED
            db.commit()
            return

        # 4. Save path and status to database
        asset.converted_pdf_path = derived_key
        asset.conversion_status = AssetConversionStatus.COMPLETED
        db.commit()
        logger.info(f"Asset {asset_id} conversion completed successfully. Converted PDF path: {derived_key}")

        # 5. Trigger ingestion directly in the same session
        try:
            from app.services.ingestion_service import ingest_asset
            logger.info(f"Triggering direct ingestion for conversion-completed asset {asset_id}...")
            ingest_asset(asset_id, db)
        except Exception as e:
            logger.exception(f"Unexpected error when triggering ingestion for asset {asset_id}: {e}")

    except Exception as e:
        logger.exception(f"Unexpected error during background conversion of asset {asset_id}: {e}")
        try:
            db.rollback()
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if asset:
                asset.conversion_status = AssetConversionStatus.FAILED
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to set status to FAILED in DB after unexpected exception: {db_err}")
    finally:
        # Check if asset conversion failed, update ingestion status to FAILED
        try:
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if asset and asset.conversion_status == AssetConversionStatus.FAILED:
                if asset.ingestion_status != AssetIngestionStatus.FAILED or asset.ingestion_error != "CONVERSION_FAILED":
                    asset.ingestion_status = AssetIngestionStatus.FAILED
                    asset.ingestion_error = "CONVERSION_FAILED"
                    db.commit()
                    logger.info(f"Asset {asset_id} ingestion marked as FAILED due to conversion failure.")
        except Exception as e:
            logger.error(f"Error setting ingestion failure metadata for asset {asset_id}: {e}")
        db.close()
