import sys
import os
import io
import time
import zipfile
import logging
from fastapi.testclient import TestClient

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.main import app
from app.core.database import SessionLocal
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.notebook import Notebook
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_ingestion_pipeline")


def create_dummy_docx() -> bytes:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    document = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:r>
        <w:t>Hello World! Day la tai lieu kiem thu thuc te. Kỹ thuật lập trình và cấu trúc dữ liệu giải thuật học máy và mô hình ngôn ngữ lớn.</w:t>
      </w:r>
    </w:p>
  </w:body>
</w:document>"""

    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
    return out.getvalue()


def run_tests():
    client = TestClient(app)
    
    # 1. Register & Login test user
    email = f"test_e2e_{int(time.time())}@example.com"
    password = "PipelineUser123!"
    full_name = "Pipeline Test User"
    
    # Register
    reg_resp = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    assert reg_resp.status_code == 201, f"Reg failed: {reg_resp.text}"
    token_data = reg_resp.json()
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test notebook
    nb_resp = client.post("/notebooks", json={
        "title": "E2E Test Notebook",
        "description": "Notebook for testing pipeline"
    }, headers=headers)
    assert nb_resp.status_code == 201, f"Notebook creation failed: {nb_resp.text}"
    notebook_id = nb_resp.json()["id"]
    
    db = SessionLocal()
    try:
        # ==========================================
        # TEST 1: PDF Ingestion Success
        # ==========================================
        logger.info("--- TEST 1: PDF Upload & Ingestion Polling ---")
        pdf_path = os.path.join(backend_dir, "app", "seed_assets", "KTLT_Chapter1_nDArray.pdf")
        assert os.path.exists(pdf_path), f"Sample PDF not found at {pdf_path}"
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
            
        files = {"file": ("KTLT_Chapter1_nDArray.pdf", pdf_bytes, "application/pdf")}
        upload_resp = client.post(f"/notebooks/{notebook_id}/assets", files=files, headers=headers)
        assert upload_resp.status_code == 201, f"PDF upload failed: {upload_resp.text}"
        asset_id = upload_resp.json()["id"]
        
        # Poll status
        status_completed = False
        for i in range(15):
            time.sleep(1)
            status_resp = client.get(f"/notebooks/{notebook_id}/assets/{asset_id}/status", headers=headers)
            assert status_resp.status_code == 200
            data = status_resp.json()
            logger.info(f"PDF Ingestion Status Poll {i+1}: status={data['ingestion_status']}, chunk_count={data['chunk_count']}")
            if data["ingestion_status"] == "COMPLETED":
                status_completed = True
                assert data["chunk_count"] > 0
                break
            elif data["ingestion_status"] == "FAILED":
                raise RuntimeError(f"Ingestion failed: {data['ingestion_error']}")
                
        assert status_completed, "PDF Ingestion timed out or did not complete"
        
        # Check DB embeddings
        from sqlalchemy import select
        db.expire_all()
        embeddings = db.execute(select(AssetEmbedding).where(AssetEmbedding.asset_id == asset_id)).scalars().all()
        assert len(embeddings) > 0, "No embeddings saved in DB"
        logger.info(f"Verified Test 1: Created {len(embeddings)} chunks with embeddings in DB.")
        
        # ==========================================
        # TEST 2: DOCX Conversion -> Ingestion Flow
        # ==========================================
        logger.info("--- TEST 2: DOCX Upload, Conversion & Ingestion ---")
        docx_bytes = create_dummy_docx()
        files = {"file": ("test_doc.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        upload_docx_resp = client.post(f"/notebooks/{notebook_id}/assets", files=files, headers=headers)
        assert upload_docx_resp.status_code == 201, f"DOCX upload failed: {upload_docx_resp.text}"
        docx_asset_id = upload_docx_resp.json()["id"]
        
        # Poll status
        status_completed = False
        for i in range(25):
            time.sleep(2)
            status_resp = client.get(f"/notebooks/{notebook_id}/assets/{docx_asset_id}/status", headers=headers)
            assert status_resp.status_code == 200
            data = status_resp.json()
            logger.info(f"DOCX Ingestion Status Poll {i+1}: status={data['ingestion_status']}, chunk_count={data['chunk_count']}, error={data['ingestion_error']}")
            
            # Fetch conversion status from DB to log info
            asset_db = db.query(Asset).filter(Asset.id == docx_asset_id).first()
            if asset_db:
                logger.info(f"  - DB states: conversion_status={asset_db.conversion_status.value if asset_db.conversion_status else None}, ingestion_status={asset_db.ingestion_status.value if asset_db.ingestion_status else None}")
                
            if data["ingestion_status"] == "COMPLETED":
                status_completed = True
                assert data["chunk_count"] > 0
                break
            elif data["ingestion_status"] == "FAILED":
                raise RuntimeError(f"DOCX Ingestion and/or Conversion failed: {data['ingestion_error']}")
                
        assert status_completed, "DOCX Ingestion/Conversion timed out or did not complete"
        
        db.expire_all()
        docx_embeddings = db.execute(select(AssetEmbedding).where(AssetEmbedding.asset_id == docx_asset_id)).scalars().all()
        assert len(docx_embeddings) > 0, "No embeddings saved in DB for DOCX asset"
        logger.info(f"Verified Test 2: Created {len(docx_embeddings)} chunks with embeddings in DB for DOCX.")
        
        # ==========================================
        # TEST 3: Access Control & Invalid Notebook
        # ==========================================
        logger.info("--- TEST 3: Access Control Checks ---")
        # Try to pull status with invalid/unauthorized header (using different user or no headers)
        other_user_email = f"other_{int(time.time())}@example.com"
        reg_resp2 = client.post("/auth/register", json={
            "email": other_user_email,
            "password": password,
            "full_name": "Other User"
        })
        other_token = reg_resp2.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # Accessing first user's asset with other user's token should yield forbidden 403
        unauthorized_resp = client.get(f"/notebooks/{notebook_id}/assets/{asset_id}/status", headers=other_headers)
        assert unauthorized_resp.status_code == 403, f"Expected 403 Forbidden, got {unauthorized_resp.status_code}: {unauthorized_resp.text}"
        logger.info("Verified Test 3: Unauthorized user access correctly forbidden (403).")
        
        # Accessing non-exist notebook should yield 404
        nonexist_resp = client.get(f"/notebooks/99999/assets/{asset_id}/status", headers=headers)
        assert nonexist_resp.status_code == 404, f"Expected 404, got {nonexist_resp.status_code}"
        logger.info("Verified Test 3: Non-existent notebook request correctly not found (404).")

        logger.info("ALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
        
    finally:
        # Clean up test user & notebook & assets
        try:
            # Query & delete created records to keep db clean
            db.expire_all()
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.execute(AssetEmbedding.__table__.delete().where(AssetEmbedding.asset_id.in_([asset_id, docx_asset_id])))
                db.execute(Asset.__table__.delete().where(Asset.id.in_([asset_id, docx_asset_id])))
                db.execute(Notebook.__table__.delete().where(Notebook.id == notebook_id))
                db.delete(user)
            other_user = db.query(User).filter(User.email == other_user_email).first()
            if other_user:
                db.delete(other_user)
            db.commit()
            logger.info("Cleaned up E2E test data from database.")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
            db.rollback()
        db.close()


if __name__ == "__main__":
    run_tests()
