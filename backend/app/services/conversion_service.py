from __future__ import annotations

import logging
import os
import subprocess
import tempfile
import shutil

from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.enums import AssetConversionStatus
from app.services import storage_service
from app.services.storage_service import get_minio_client

logger = logging.getLogger(__name__)


def convert_docx_to_pdf_task(asset_id: int) -> None:
    """
    Background task to download a DOCX file from MinIO, convert it to PDF using soffice,
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
            from app.core.config import settings
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

        # 2. Run conversion using soffice in a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_docx_path = os.path.join(tmpdir, "input.docx")
            with open(input_docx_path, "wb") as f:
                f.write(docx_data)

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
                input_docx_path
            ]

            logger.info(f"Running LibreOffice conversion cmd: {' '.join(cmd)}")
            try:
                # Use subprocess.run with timeout (60 seconds)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
                logger.info(f"LibreOffice stdout: {result.stdout}")
                logger.info(f"LibreOffice stderr: {result.stderr}")
            except subprocess.TimeoutExpired as e:
                logger.error(f"LibreOffice conversion timed out for asset {asset_id}: {e}")
                asset.conversion_status = AssetConversionStatus.FAILED
                db.commit()
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"LibreOffice conversion process error for asset {asset_id}: exit code {e.returncode}. stdout: {e.stdout}, stderr: {e.stderr}")
                asset.conversion_status = AssetConversionStatus.FAILED
                db.commit()
                return
            except FileNotFoundError:
                logger.error("soffice binary not found in system PATH.")
                asset.conversion_status = AssetConversionStatus.FAILED
                db.commit()
                return

            expected_pdf_path = os.path.join(tmpdir, "input.pdf")
            if not os.path.exists(expected_pdf_path):
                logger.error(f"Conversion command ran but output PDF not found at {expected_pdf_path}")
                asset.conversion_status = AssetConversionStatus.FAILED
                db.commit()
                return

            # Read converted PDF
            with open(expected_pdf_path, "rb") as f:
                pdf_data = f.read()

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

            # Trigger ingestion directly in the same session
            try:
                from app.services.ingestion_service import ingest_asset
                logger.info(f"Triggering direct ingestion for conversion-completed asset {asset_id}...")
                ingest_asset(asset_id, db)
            except Exception as e:
                logger.exception(f"Unexpected error when triggers ingestion for asset {asset_id}: {e}")

    except Exception as e:
        logger.exception(f"Unexpected error during background conversion of asset {asset_id}: {e}")
        try:
            db.rollback()
            # Try to mark the asset as failed
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
                from app.models.enums import AssetIngestionStatus
                if asset.ingestion_status != AssetIngestionStatus.FAILED or asset.ingestion_error != "CONVERSION_FAILED":
                    asset.ingestion_status = AssetIngestionStatus.FAILED
                    asset.ingestion_error = "CONVERSION_FAILED"
                    db.commit()
                    logger.info(f"Asset {asset_id} ingestion marked as FAILED due to conversion failure.")
        except Exception as e:
            logger.error(f"Error setting ingestion failure metadata for asset {asset_id}: {e}")
        db.close()
