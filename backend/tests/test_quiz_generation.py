import os
import sys
import time
import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pydantic import ValidationError

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
from app.schemas.artifact import QuizQuestion, QuizOption, QuizContentPayload
from app.services.quiz_service import linear_space_sampling, extract_context_from_assets

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_quiz_generation")


# =====================================================================
# UNIT TESTS: Linear Space Sampling
# =====================================================================

def test_linear_space_sampling_various_chunks():
    logger.info("--- UNIT TEST: linear_space_sampling ---")
    mock_chunks = [AssetEmbedding(id=i, chunk_index=i, content=f"chunk {i}", page_number=1) for i in range(100)]

    # Test case 1: total chunks <= budget
    result = linear_space_sampling(mock_chunks[:5], budget_per_asset=10)
    assert len(result) == 5
    assert result == mock_chunks[:5]

    # Test case 2: budget_per_asset == 1
    result = linear_space_sampling(mock_chunks[:20], budget_per_asset=1)
    assert len(result) == 1
    assert result[0].chunk_index == 0

    # Test case 3: budget_per_asset > 1
    # total chunks 20, budget 5 -> check indices
    result = linear_space_sampling(mock_chunks[:20], budget_per_asset=5)
    assert len(result) == 5
    # indices: round(i * 19 / 4) for i in 0..4 -> 0, 5, 10, 14, 19
    expected_indices = [0, 5, 10, 14, 19]
    assert [c.chunk_index for c in result] == expected_indices
    # Ensure first and last chunks are included
    assert result[0].chunk_index == 0
    assert result[-1].chunk_index == 19

    # Test case 4: large chunk size (100) and budget 10
    result = linear_space_sampling(mock_chunks, budget_per_asset=10)
    assert len(result) == 10
    assert result[0].chunk_index == 0
    assert result[-1].chunk_index == 99


# =====================================================================
# UNIT TESTS: Pydantic Schema Validator
# =====================================================================

def test_quiz_question_options_validation():
    logger.info("--- UNIT TEST: QuizQuestion options validation ---")

    # Valid options
    valid_opts = [
        QuizOption(key="A", text="Opt A"),
        QuizOption(key="B", text="Opt B"),
        QuizOption(key="C", text="Opt C"),
        QuizOption(key="D", text="Opt D")
    ]

    question = QuizQuestion(
        id=1,
        question="What is Python?",
        options=valid_opts,
        correct_answer="A",
        explanation="Python is awesome"
    )
    assert question.id == 1

    # Invalid options: duplicates (A, B, B, C)
    invalid_opts_dup = [
        QuizOption(key="A", text="Opt A"),
        QuizOption(key="B", text="Opt B1"),
        QuizOption(key="B", text="Opt B2"),
        QuizOption(key="C", text="Opt C")
    ]
    try:
        QuizQuestion(
            id=2,
            question="What is Python?",
            options=invalid_opts_dup,
            correct_answer="A",
            explanation="Bad"
        )
        assert False, "Expected ValidationError for duplicates but none was raised"
    except ValidationError as e:
        assert "Quiz options must contain exactly the keys: A, B, C, D" in str(e)

    # Invalid options: count is not 4
    invalid_opts_count = [
        QuizOption(key="A", text="Opt A"),
        QuizOption(key="B", text="Opt B"),
        QuizOption(key="C", text="Opt C")
    ]
    try:
        QuizQuestion(
            id=3,
            question="What is Python?",
            options=invalid_opts_count,
            correct_answer="A",
            explanation="Bad"
        )
        assert False, "Expected ValidationError for invalid options count but none was raised"
    except ValidationError as e:
        assert "List should have at least 4 items" in str(e)


# =====================================================================
# INTEGRATION TESTS: RAG API Generation (Mocked Gemini Call)
# =====================================================================

def test_integration_quiz_generation():
    client = TestClient(app)

    # Register & Login test user
    email = f"rag_test_{int(time.time())}@example.com"
    password = "UserPassword123!"

    reg_resp = client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "RAG Quiz Agent Test"
    })
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create notebook
    nb_resp = client.post("/notebooks", json={
        "title": "RAG Test Notebook",
        "description": "Notebook for testing RAG generator"
    }, headers=headers)
    assert nb_resp.status_code == 201
    notebook_id = nb_resp.json()["id"]

    db = SessionLocal()
    try:
        # Seed completed assets direct and embeddings direct in DB
        asset = Asset(
            notebook_id=notebook_id,
            file_name="rag_lecture.pdf",
            file_path="mock/path/rag_lecture.pdf",
            file_type="application/pdf",
            size=4096,
            ingestion_status=AssetIngestionStatus.COMPLETED
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        # Create multiple embeddings
        embeddings = []
        for i in range(10):
            emb = AssetEmbedding(
                asset_id=asset.id,
                chunk_index=i,
                content=f"This is chunk content number {i} containing important information about topic X.",
                page_number=i // 3 + 1,
            )
            embeddings.append(emb)
            db.add(emb)
        db.commit()

        # Mock the Google GenAI Native call
        mock_quiz_payload = QuizContentPayload(
            title="Sách Học Tập Đại Cương Quiz",
            questions=[
                QuizQuestion(
                    id=1,
                    question="Câu hỏi 1 từ tài liệu?",
                    options=[
                        QuizOption(key="A", text="Đáp án A"),
                        QuizOption(key="B", text="Đáp án B"),
                        QuizOption(key="C", text="Đáp án C"),
                        QuizOption(key="D", text="Đáp án D")
                    ],
                    correct_answer="A",
                    explanation="Giải thích A đúng"
                )
            ]
        )

        with patch("app.services.quiz_service._call_gemini_with_retry", return_value=mock_quiz_payload) as mock_gemini:
            # Let's test context extraction works first
            context = extract_context_from_assets(db, [asset.id])
            assert "rag_lecture.pdf" in context
            assert "This is chunk content number 0" in context

            payload = {
                "selected_asset_ids": [asset.id],
                "num_questions": 1
            }

            logger.info("--- INTEGRATION TEST: POST /artifacts/generate (success) ---")
            resp = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers)
            assert resp.status_code == 201
            data = resp.json()
            assert data["title"] == "Sách Học Tập Đại Cương Quiz"
            assert data["total_items"] == 1
            assert len(data["content"]["questions"]) == 1
            artifact_id = data["id"]

            # Verify cooldown 429
            logger.info("--- INTEGRATION TEST: POST /artifacts/generate (cooldown) ---")
            resp_cooldown = client.post(f"/notebooks/{notebook_id}/artifacts/generate", json=payload, headers=headers)
            assert resp_cooldown.status_code == 429
            assert "Thao tác quá nhanh" in resp_cooldown.json()["detail"]

    finally:
        # DB clean up
        db.expire_all()
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.delete(u)
        db.commit()
        db.close()


def run_all_tests():
    # Run functions manually
    test_linear_space_sampling_various_chunks()
    test_quiz_question_options_validation()
    test_integration_quiz_generation()
    logger.info("ALL TEST CASES COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_tests()
