import os
import sys
import time
import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set environment overrides to connect locally if not set
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("MINIO_HOST", "localhost")

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.main import app
from app.core.database import SessionLocal
from app.models.notebook import Notebook
from app.models.artifact import NotebookArtifact
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.enums import AssetIngestionStatus, ArtifactType
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_notebook_artifact")


def run_tests():
    client = TestClient(app)

    # 1. Register & Login test user 1
    email_u1 = f"art_test_u1_{int(time.time())}@example.com"
    password = "UserPassword123!"

    reg_resp1 = client.post("/auth/register", json={
        "email": email_u1,
        "password": password,
        "full_name": "Artifact Test User 1"
    })
    assert reg_resp1.status_code == 201, f"Reg 1 failed: {reg_resp1.text}"
    token_u1 = reg_resp1.json()["access_token"]
    headers_u1 = {"Authorization": f"Bearer {token_u1}"}

    # Register & Login test user 2 (for testing ownership checks)
    email_u2 = f"art_test_u2_{int(time.time())}@example.com"
    reg_resp2 = client.post("/auth/register", json={
        "email": email_u2,
        "password": password,
        "full_name": "Artifact Test User 2"
    })
    assert reg_resp2.status_code == 201, f"Reg 2 failed: {reg_resp2.text}"
    token_u2 = reg_resp2.json()["access_token"]
    headers_u2 = {"Authorization": f"Bearer {token_u2}"}

    # Create notebook for user 1
    nb_resp = client.post("/notebooks", json={
        "title": "U1 Artifact Notebook",
        "description": "Notebook for testing artifact operations"
    }, headers=headers_u1)
    assert nb_resp.status_code == 201, f"Notebook creation failed: {nb_resp.text}"
    notebook_id = nb_resp.json()["id"]

    db = SessionLocal()
    try:
        # Seed positive completed assets for user 1 notebook inside DB
        logger.info("Seeding COMPLETED assets directly in database...")
        asset1 = Asset(
            notebook_id=notebook_id,
            file_name="lecture1.pdf",
            file_path="mock/path/lecture1.pdf",
            file_type="application/pdf",
            size=1024,
            ingestion_status=AssetIngestionStatus.COMPLETED
        )
        asset2 = Asset(
            notebook_id=notebook_id,
            file_name="lecture2.pdf",
            file_path="mock/path/lecture2.pdf",
            file_type="application/pdf",
            size=2048,
            ingestion_status=AssetIngestionStatus.PENDING # Pending status to test asset check guard
        )
        db.add(asset1)
        db.add(asset2)
        db.commit()
        db.refresh(asset1)
        db.refresh(asset2)

        emb1 = AssetEmbedding(
            asset_id=asset1.id,
            chunk_index=0,
            content="Nội dung bài giảng số 1 về cấu trúc dữ liệu và giải thuật trong khoa học máy tính.",
            page_number=1,
            token_count=20,
        )
        db.add(emb1)
        db.commit()

        # ==========================================
        # TEST 1: Generate Quiz (Asset Validation Fails)
        # ==========================================
        logger.info("--- TEST 1: Generate Quiz with PENDING asset (should fail) ---")
        payload = {
            "selected_asset_ids": [asset1.id, asset2.id],
            "num_questions": 5
        }
        resp = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers_u1)
        assert resp.status_code == 400
        assert "Tất cả tài liệu được tuyển chọn phải được xử lý thành công" in resp.json()["detail"]

        # ==========================================
        # TEST 2: Generate Quiz (Success)
        # ==========================================
        logger.info("--- TEST 2: Generate Quiz (Success) ---")
        payload = {
            "selected_asset_ids": [asset1.id],
            "num_questions": 5
        }
        resp = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers_u1)
        import sys
        sys.stdout.buffer.write(b"GENERATE RESPONSE DETAIL: " + resp.content + b"\n")
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["title"]) > 0
        assert len(data["content"]["questions"]) == 5
        assert data["total_items"] == 5 # Overridden computed property counts length of questions
        artifact_id = data["id"]

        # ==========================================
        # TEST 3: Cooldown Guard (15s)
        # ==========================================
        logger.info("--- TEST 3: Generate Quiz too quickly (cooldown active) ---")
        resp_cooldown = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers_u1)
        assert resp_cooldown.status_code == 429
        assert "Thao tác quá nhanh" in resp_cooldown.json()["detail"]

        # ==========================================
        # TEST 4: Quota Guard (20 limit)
        # ==========================================
        logger.info("--- TEST 4: Quota Guard (Adding 20 mock artifacts) ---")
        from datetime import datetime, timedelta, timezone
        past_time = datetime.now(timezone.utc) - timedelta(seconds=60)
        existing_artifacts = db.query(NotebookArtifact).filter(NotebookArtifact.notebook_id == notebook_id).all()
        for art in existing_artifacts:
            art.created_at = past_time

        # Bypass cooldown by inserting records directly to DB
        for i in range(19): # already have 1, total will be 20
            mock_art = NotebookArtifact(
                notebook_id=notebook_id,
                user_id=db.query(User).filter(User.email == email_u1).first().id,
                title=f"Mock Artifact {i}",
                artifact_type=ArtifactType.QUIZ,
                content={"title": "Quiz", "questions": []},
                metadata_={"selected_asset_ids": [asset1.id], "num_questions": 5},
                created_at=past_time
            )
            db.add(mock_art)
        db.commit()

        # Try to create the 21st, should fail
        resp_quota = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers_u1)
        assert resp_quota.status_code == 400
        assert "Notebook đã đạt giới hạn tối đa 20 bài tập" in resp_quota.json()["detail"]

        # ==========================================
        # TEST 5: Ownership Guard (404 / 403 on generate)
        # ==========================================
        logger.info("--- TEST 5: Ownership Guard Control ---")
        # User 2 tries to generate quiz in User 1's notebook -> expect 403 (Notebook owned by User 1 but requested by User 2)
        resp_unauth = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers_u2)
        assert resp_unauth.status_code == 403

        # Non-existent notebook -> expect 404
        resp_fake = client.post(f"/notebooks/99999/artifacts/generate", json=payload, headers=headers_u1)
        assert resp_fake.status_code == 404

        # ==========================================
        # TEST 6: List Artifacts (Summary Response & Defer Content)
        # ==========================================
        logger.info("--- TEST 6: List Artifacts (No content field) ---")
        list_resp = client.get(f"/notebooks/{notebook_id}/artifacts", headers=headers_u1)
        assert list_resp.status_code == 200
        arts = list_resp.json()
        assert len(arts) == 20
        # Ensure that content is not in summary responses (FastAPI filters out fields not in schema, and deferred database I/O is applied)
        for art in arts:
            assert "content" not in art
            assert art["total_items"] == 5 # Read safely from metadata

        # ==========================================
        # TEST 7: Get Artifact Detail
        # ==========================================
        logger.info("--- TEST 7: Get Artifact Detail ---")
        detail_resp = client.get(f"/notebooks/{notebook_id}/artifacts/{artifact_id}", headers=headers_u1)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert "content" in detail
        assert len(detail["content"]["questions"]) == 5
        assert detail["total_items"] == 5

        # Try to access with user 2 -> expect 403
        detail_unauth = client.get(f"/notebooks/{notebook_id}/artifacts/{artifact_id}", headers=headers_u2)
        assert detail_unauth.status_code == 403

        # ==========================================
        # TEST 8: Delete Artifact
        # ==========================================
        logger.info("--- TEST 8: Delete Artifact ---")
        del_resp = client.delete(f"/notebooks/{notebook_id}/artifacts/{artifact_id}", headers=headers_u1)
        assert del_resp.status_code == 200
        assert del_resp.json() == {"status": "deleted"}

        # Verify deletion in DB
        db.expire_all()
        check_art = db.get(NotebookArtifact, artifact_id)
        assert check_art is None

        logger.info("ALL NOTEBOOK ARTIFACT MOCK TESTS PASSED SUCCESSFULLY!")

    finally:
        # Clean up database records
        try:
            logger.info("Cleaning up database test records...")
            db.expire_all()
            u1 = db.query(User).filter(User.email == email_u1).first()
            if u1:
                db.delete(u1)
            u2 = db.query(User).filter(User.email == email_u2).first()
            if u2:
                db.delete(u2)
            db.commit()
            logger.info("Database cleaned up successfully.")
        except Exception as e:
            logger.warning(f"Error during test cleanup: {e}")
            db.rollback()
        db.close()


if __name__ == "__main__":
    run_tests()
