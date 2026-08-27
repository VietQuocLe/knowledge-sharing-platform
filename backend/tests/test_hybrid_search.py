import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Set environment overrides to connect locally (outside Docker)
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["MINIO_HOST"] = "localhost"

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models.user import User
from app.models.notebook import Notebook, NotebookSavedDocument
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.models.enums import AssetIngestionStatus, AssetConversionStatus
from app.services.retrieval_service import hybrid_retrieval, get_scoped_asset_ids

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_hybrid_search")


def run_tests():
    db = SessionLocal()
    
    # 0. Clean up old test records to avoid contamination
    logger.info("Cleaning up old test users...")
    old_users = db.query(User).filter(User.email.like("rrf_test_%")).all()
    for u in old_users:
        db.delete(u)
    db.commit()

    try:
        # 1. Create Test Users
        user_a = User(email="rrf_test_a@example.com", password_hash="hashed_pw_1", full_name="User A")
        user_b = User(email="rrf_test_b@example.com", password_hash="hashed_pw_2", full_name="User B")
        db.add_all([user_a, user_b])
        db.commit()
        db.refresh(user_a)
        db.refresh(user_b)

        # 2. Create Notebooks
        nb_a = Notebook(title="Notebook A", owner_id=user_a.id)
        nb_b = Notebook(title="Notebook B", owner_id=user_b.id)
        nb_empty = Notebook(title="Notebook Empty", owner_id=user_a.id)
        db.add_all([nb_a, nb_b, nb_empty])
        db.commit()
        db.refresh(nb_a)
        db.refresh(nb_b)
        db.refresh(nb_empty)

        # 3. Create completed / pending assets for Notebook A
        asset_a1 = Asset(
            notebook_id=nb_a.id,
            file_name="ktlt_doc.pdf",
            file_path="notebooks/1/ktlt_doc.pdf",
            file_type="application/pdf",
            size=1234,
            ingestion_status=AssetIngestionStatus.COMPLETED
        )
        asset_a2_pending = Asset(
            notebook_id=nb_a.id,
            file_name="pending_doc.pdf",
            file_path="notebooks/1/pending_doc.pdf",
            file_type="application/pdf",
            size=5000,
            ingestion_status=AssetIngestionStatus.PENDING # Should NOT be retrieved
        )
        db.add_all([asset_a1, asset_a2_pending])
        db.commit()
        db.refresh(asset_a1)
        db.refresh(asset_a2_pending)

        # 4. Create completed asset for Notebook B (to test data isolation)
        asset_b1 = Asset(
            notebook_id=nb_b.id,
            file_name="software_arch.pdf",
            file_path="notebooks/2/software_arch.pdf",
            file_type="application/pdf",
            size=5678,
            ingestion_status=AssetIngestionStatus.COMPLETED
        )
        db.add(asset_b1)
        db.commit()
        db.refresh(asset_b1)

        # 5. Populate embeddings for Asset A1 (Notebook A)
        # We write 3 sequential chunks on Page 1 (should stitch), and 1 chunk on Page 2 (separate block)
        emb_a1_1 = AssetEmbedding(
            asset_id=asset_a1.id,
            chunk_index=0,
            content="Học máy là một lĩnh vực của trí tuệ nhân tạo.",
            embedding=[0.11] * 768,
            page_number=1
        )
        emb_a1_2 = AssetEmbedding(
            asset_id=asset_a1.id,
            chunk_index=1,
            content="Nó cho phép máy tính tự động học hỏi từ dữ liệu dữ kiện.",
            embedding=[0.12] * 768,
            page_number=1
        )
        emb_a1_3 = AssetEmbedding(
            asset_id=asset_a1.id,
            chunk_index=2,
            content="Các thuật toán tinh vi giúp phân tích xu hướng phức tạp.",
            embedding=[0.13] * 768,
            page_number=1
        )
        emb_a1_page2 = AssetEmbedding(
            asset_id=asset_a1.id,
            chunk_index=3,
            content="Đây là nội dung ở trang số hai về mạng nơ-ron chuyên sâu.",
            embedding=[0.20] * 768,
            page_number=2
        )
        
        # Populate embeddings for Pending Asset A2 (should remain invisible)
        emb_a2_pending = AssetEmbedding(
            asset_id=asset_a2_pending.id,
            chunk_index=0,
            content="Tài liệu nháp chưa xử lý xong về trí tuệ nhân tạo.",
            embedding=[0.11] * 768,
            page_number=1
        )

        # Populate embeddings for Asset B1 (Notebook B - similar text/embedding)
        emb_b1_1 = AssetEmbedding(
            asset_id=asset_b1.id,
            chunk_index=0,
            content="Học máy và phân tích thiết kế hệ thống phần mềm.", # similar keyword
            embedding=[0.11] * 768, # matching embedding
            page_number=1
        )

        db.add_all([emb_a1_1, emb_a1_2, emb_a1_3, emb_a1_page2, emb_a2_pending, emb_b1_1])
        db.commit()

        # Refresh database structures
        db.expire_all()

        # ==========================================
        # VERIFICATION 1: Test Empty Notebook (Short circuit)
        # ==========================================
        logger.info("--- VERIFICATION 1: Empty Notebook (Short circuit) ---")
        ret_empty = hybrid_retrieval(db, notebook_id=nb_empty.id, query="học máy")
        assert ret_empty["status"] == "no_documents"
        assert len(ret_empty["chunks"]) == 0
        assert ret_empty["context"] == ""
        logger.info("Checked: Empty notebook returned early without executing DB search.")

        # ==========================================
        # VERIFICATION 2: Test Data Isolation (nb_a query should never yield nb_b chunks)
        # ==========================================
        logger.info("--- VERIFICATION 2: Query Isolation Between Notebooks ---")
        # Direct mock call to test vectors
        with patch("app.services.retrieval_service.generate_query_embedding") as mock_emb:
            mock_emb.return_value = [0.11] * 768

            # Search in Notebook A
            ret_a = hybrid_retrieval(db, notebook_id=nb_a.id, query="trí tuệ nhân tạo học máy")
            assert ret_a["status"] == "success"
            
            # None of the chunks should have asset_id == asset_b1.id
            # None of the chunks should belong to asset_a2_pending.id
            for block in ret_a["chunks"]:
                assert block["asset_id"] != asset_b1.id, "Security leak! Found Asset B chunk inside Notebook A query."
                assert block["asset_id"] != asset_a2_pending.id, "State leak! Found pending asset chunk."
                
            logger.info("Checked: Data isolation verified. Queries do not leak cross-notebook or retrieve pending assets.")

        # ==========================================
        # VERIFICATION 3: Adjacent Chunk Stitching
        # ==========================================
        logger.info("--- VERIFICATION 3: Adjacent Chunk Stitching ---")
        with patch("app.services.retrieval_service.generate_query_embedding") as mock_emb:
            mock_emb.return_value = [0.11] * 768 # close to emb_a1_1, emb_a1_2, emb_a1_3

            ret_stitch = hybrid_retrieval(db, notebook_id=nb_a.id, query="mô hình học máy dữ liệu")
            
            # The top 5 candidates will cover:
            # - emb_a1_1 (p1, idx 0)
            # - emb_a1_2 (p1, idx 1)
            # - emb_a1_3 (p1, idx 2)
            # - emb_a1_page2 (p2, idx 3)
            # Since first three are on page 1 and consecutive index, they must STITCH!
            # The result should have:
            # - 1 block for page 1 (stitched contents of a1_1 + a1_2 + a1_3)
            # - 1 block for page 2 (a1_page2)
            # Thus, total number of returned block groups is 2 (less than 5).
            
            chunks = ret_stitch["chunks"]
            assert len(chunks) == 2, f"Expected 2 stitched blocks, got {len(chunks)}"
            
            # Block 1 (Page 1) content check
            block_p1 = next(c for c in chunks if c["page_number"] == 1)
            expected_p1_text = (
                "Học máy là một lĩnh vực của trí tuệ nhân tạo. "
                "Nó cho phép máy tính tự động học hỏi từ dữ liệu dữ kiện. "
                "Các thuật toán tinh vi giúp phân tích xu hướng phức tạp."
            )
            assert block_p1["content"] == expected_p1_text, f"Stitching text mismatch: {block_p1['content']}"

            # Block 2 (Page 2) content check
            block_p2 = next(c for c in chunks if c["page_number"] == 2)
            assert block_p2["content"] == "Đây là nội dung ở trang số hai về mạng nơ-ron chuyên sâu."
            
            # Checking renumbering [1], [2] in context
            assert "[1] [Tài liệu: ktlt_doc.pdf, Trang: 1]" in ret_stitch["context"]
            assert "[2] [Tài liệu: ktlt_doc.pdf, Trang: 2]" in ret_stitch["context"]
            
            logger.info("Checked: Adjacent chunks stitched and renumbered [1]..[N] correctly.")
            logger.info(f"Stitched Context:\n{ret_stitch['context']}")

        # ==========================================
        # VERIFICATION 4: Token Budget Enforcement
        # ==========================================
        logger.info("--- VERIFICATION 4: Token Budget Enforcement ---")
        with patch("app.services.retrieval_service.generate_query_embedding") as mock_emb:
            mock_emb.return_value = [0.11] * 768
            
            # Mock Gemini count_tokens to simulate over budget
            with patch("app.services.retrieval_service.genai.Client") as mock_client_cls:
                mock_client = MagicMock()
                mock_client_cls.return_value = mock_client
                
                # Mock first call (with 2 blocks) returning > 3000 tokens
                # Mock second call (with 1 block popped) returning < 3000 tokens
                mock_count_response1 = MagicMock(total_tokens=3500)
                mock_count_response2 = MagicMock(total_tokens=1200)
                
                mock_client.models.count_tokens.side_effect = [
                    mock_count_response1,
                    mock_count_response2
                ]

                ret_budget = hybrid_retrieval(db, notebook_id=nb_a.id, query="học máy")
                
                # It should drop the second block (page 2 block) and retain only page 1 block
                assert len(ret_budget["chunks"]) == 1
                assert ret_budget["chunks"][0]["page_number"] == 1
                
                # Only renumbered [1] should remain
                assert "[1] [Tài liệu: ktlt_doc.pdf]" in ret_budget["context"] or "Trang: 1" in ret_budget["context"]
                assert "[2]" not in ret_budget["context"]
                
                logger.info("Checked: Token budget enforced. Lower RRF scores dropped correctly.")

        logger.info("ALL HYBRID RETRIEVAL PERSISTENCE INTEGRATION TESTS PASSED SUCCESSFULLY!")

    finally:
        # Clean up database records
        try:
            logger.info("Cleaning up database test records...")
            db.expire_all()
            
            # Find and delete test users (which triggers cascading deletes)
            u_a = db.query(User).filter(User.email == "rrf_test_a@example.com").first()
            if u_a:
                db.delete(u_a)
            u_b = db.query(User).filter(User.email == "rrf_test_b@example.com").first()
            if u_b:
                db.delete(u_b)
            db.commit()
            logger.info("Database cleaned up successfully.")
        except Exception as e:
            logger.warning(f"Error during test cleanup: {e}")
            db.rollback()
        db.close()


if __name__ == "__main__":
    run_tests()
