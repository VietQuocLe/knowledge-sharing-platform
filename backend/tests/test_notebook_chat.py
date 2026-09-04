import os
import sys
import time
import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set environment overrides to connect locally (outside Docker) if not set
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("MINIO_HOST", "localhost")

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.main import app
from app.core.database import SessionLocal
from app.models.notebook import Notebook
from app.models.notebook_chat import NotebookChatSession, NotebookChatMessage
from app.models.user import User

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_notebook_chat")


def run_tests():
    client = TestClient(app)
    
    # 1. Register & Login test user 1
    email_u1 = f"chat_test_u1_{int(time.time())}@example.com"
    password = "ChatUser123!"
    
    reg_resp1 = client.post("/auth/register", json={
        "email": email_u1,
        "password": password,
        "full_name": "Chat Test User 1"
    })
    assert reg_resp1.status_code == 201, f"Reg 1 failed: {reg_resp1.text}"
    token_u1 = reg_resp1.json()["access_token"]
    headers_u1 = {"Authorization": f"Bearer {token_u1}"}
    
    # Register & Login test user 2 (for testing ownership checks)
    email_u2 = f"chat_test_u2_{int(time.time())}@example.com"
    reg_resp2 = client.post("/auth/register", json={
        "email": email_u2,
        "password": password,
        "full_name": "Chat Test User 2"
    })
    assert reg_resp2.status_code == 201, f"Reg 2 failed: {reg_resp2.text}"
    token_u2 = reg_resp2.json()["access_token"]
    headers_u2 = {"Authorization": f"Bearer {token_u2}"}
    
    # Create notebook for user 1
    nb_resp = client.post("/notebooks", json={
        "title": "U1 Notebook",
        "description": "Notebook for testing chat operations"
    }, headers=headers_u1)
    assert nb_resp.status_code == 201, f"Notebook creation failed: {nb_resp.text}"
    notebook_id = nb_resp.json()["id"]
    
    db = SessionLocal()
    try:
        # ==========================================
        # TEST 1: Create Session
        # ==========================================
        logger.info("--- TEST 1: Create Chat Session ---")
        sess_resp = client.post(
            f"/notebooks/{notebook_id}/sessions",
            json={"title": "Custom Test Session"},
            headers=headers_u1
        )
        assert sess_resp.status_code == 201, f"Create session failed: {sess_resp.text}"
        session_data = sess_resp.json()
        assert session_data["title"] == "Custom Test Session"
        assert session_data["notebook_id"] == notebook_id
        session_id = session_data["id"]

        # Create session with default title
        sess_default_resp = client.post(
            f"/notebooks/{notebook_id}/sessions",
            json={},
            headers=headers_u1
        )
        assert sess_default_resp.status_code == 201
        assert sess_default_resp.json()["title"] == "Phiên trò chuyện mới"
        default_session_id = sess_default_resp.json()["id"]

        # ==========================================
        # TEST 2: List Sessions
        # ==========================================
        logger.info("--- TEST 2: List Chat Sessions ---")
        list_resp = client.get(f"/notebooks/{notebook_id}/sessions", headers=headers_u1)
        assert list_resp.status_code == 200
        sessions = list_resp.json()
        assert len(sessions) == 2
        # Verify ordering (default_session flag should be first due to recently updated)
        assert sessions[0]["id"] == default_session_id

        # ==========================================
        # TEST 3: Rename Session
        # ==========================================
        logger.info("--- TEST 3: Rename Chat Session ---")
        rename_resp = client.patch(
            f"/notebooks/{notebook_id}/sessions/{session_id}",
            json={"title": "Renamed Test Session"},
            headers=headers_u1
        )
        assert rename_resp.status_code == 200
        assert rename_resp.json()["title"] == "Renamed Test Session"

        # Check in DB
        db.expire_all()
        sess_db = db.get(NotebookChatSession, session_id)
        assert sess_db is not None
        assert sess_db.title == "Renamed Test Session"

        # ==========================================
        # TEST 4: Add Messages (Blocked via API) & DB Manual Seeding
        # ==========================================
        logger.info("--- TEST 4: Add Messages (Blocked via API) & DB Manual Seeding ---")
        
        # Verify direct message posting is disabled (returns 403 Forbidden)
        msg_payload = {
            "role": "user",
            "content": "Làm thế nào để sử dụng numpy?",
            "citations": None,
            "condensed_query": "Numpy usages"
        }
        msg_resp = client.post(
            f"/notebooks/{notebook_id}/sessions/{default_session_id}/messages",
            json=msg_payload,
            headers=headers_u1
        )
        assert msg_resp.status_code == 403
        assert "Direct message creation is disabled" in msg_resp.json()["detail"]
        logger.info("Direct message creation blocked with 403 Forbidden as expected.")
        
        # Add messages directly to the database to support subsequent list/cascade tests
        msg1 = NotebookChatMessage(
            session_id=default_session_id,
            role="user",
            content="Làm thế nào để sử dụng thư viện numpy trong Python?",
            citations=None,
            condensed_query="Numpy Python usages"
        )
        msg2 = NotebookChatMessage(
            session_id=default_session_id,
            role="assistant",
            content="Để sử dụng numpy, hãy chạy lệnh import numpy as np.",
            citations=[{"source": "numpy documentation", "pages": [1]}],
            condensed_query=None
        )
        db.add(msg1)
        db.add(msg2)
        db.commit()
        
        # Mock auto-titling function call directly since the endpoint is not triggering it
        with patch("app.rag.chat.service.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_resp = MagicMock()
            mock_resp.text = "Tiêu đề Học máy nâng cao"
            mock_client.models.generate_content.return_value = mock_resp
            
            # Execute auto-titling service method directly
            from app.rag.chat.service import auto_title_session_task
            auto_title_session_task(default_session_id)
            
            db.expire_all()
            updated_sess = db.get(NotebookChatSession, default_session_id)
            assert updated_sess.title == "Tiêu đề Học máy nâng cao"
            logger.info(f"Auto-titling verified: Session title is now '{updated_sess.title}'")

        # ==========================================
        # TEST 5: Get Message History
        # ==========================================
        logger.info("--- TEST 5: Get Message History ---")
        history_resp = client.get(
            f"/notebooks/{notebook_id}/sessions/{default_session_id}/messages",
            headers=headers_u1
        )
        assert history_resp.status_code == 200
        msgs = history_resp.json()
        assert len(msgs) == 2
        # Check ordering: first message first, second message second
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

        # ==========================================
        # TEST 6: Ownership Guards (HTTP 404)
        # ==========================================
        logger.info("--- TEST 6: Ownership Guard Controls ---")
        # User 2 tries to access User 1's notebook chats -> expect 404
        unauth_sess_resp = client.post(
            f"/notebooks/{notebook_id}/sessions",
            json={"title": "Should fail"},
            headers=headers_u2
        )
        assert unauth_sess_resp.status_code == 404, f"Expected 404, got {unauth_sess_resp.status_code}"

        unauth_list_resp = client.get(f"/notebooks/{notebook_id}/sessions", headers=headers_u2)
        assert unauth_list_resp.status_code == 404

        unauth_history_resp = client.get(
            f"/notebooks/{notebook_id}/sessions/{default_session_id}/messages",
            headers=headers_u2
        )
        assert unauth_history_resp.status_code == 404

        unauth_rename_resp = client.patch(
            f"/notebooks/{notebook_id}/sessions/{default_session_id}",
            json={"title": "Hacked Title"},
            headers=headers_u2
        )
        assert unauth_rename_resp.status_code == 404

        # Access with invalid session ID but valid notebook -> expect 404
        invalid_sess_resp = client.get(
            f"/notebooks/{notebook_id}/sessions/999999/messages",
            headers=headers_u1
        )
        assert invalid_sess_resp.status_code == 404

        # ==========================================
        # TEST 7: Delete Session & Cascade Delete Verify
        # ==========================================
        logger.info("--- TEST 7: Delete Session & Cascading ---")
        del_resp = client.delete(
            f"/notebooks/{notebook_id}/sessions/{default_session_id}",
            headers=headers_u1
        )
        assert del_resp.status_code == 204

        # Verify that session is deleted
        db.expire_all()
        sess_check = db.get(NotebookChatSession, default_session_id)
        assert sess_check is None

        # Verify that messages in the session are deleted (cascade)
        from sqlalchemy import select
        db_messages = db.execute(
            select(NotebookChatMessage).where(NotebookChatMessage.session_id == default_session_id)
        ).scalars().all()
        assert len(db_messages) == 0, f"Cascading failed, messages still exist: {db_messages}"
        logger.info("Cascaded message deletion verified successfully! (0 messages remain)")

        logger.info("ALL CHAT PERSISTENCE INTEGRATION TESTS PASSED SUCCESSFULLY!")

    finally:
        # Clean up database records
        try:
            logger.info("Cleaning up database test records...")
            db.expire_all()
            
            # Find and delete test users (cascades will delete notebooks and sessions)
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


def test_notebook_chat():
    run_tests()


if __name__ == "__main__":
    run_tests()
