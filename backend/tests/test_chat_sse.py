import os
import sys
import logging
import asyncio
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set environment overrides to connect locally (outside Docker)
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["POSTGRES_PORT"] = "5433"
os.environ["MINIO_HOST"] = "localhost"

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.notebook import Notebook
from app.models.asset import Asset
from app.models.enums import AssetIngestionStatus
from app.services.notebook_chat_service import get_session_lock, stream_chat_response
from app.core.security import create_access_token

def create_mock_genai_client():
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value.text = "Mock Chat Title"
    return mock_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_chat_sse")


async def run_tests():
    db = SessionLocal()
    
    # 0. Clean up old test records to avoid contamination
    logger.info("Cleaning up old test users...")
    old_users = db.query(User).filter(User.email.like("sse_test_%")).all()
    for u in old_users:
        db.delete(u)
    db.commit()

    try:
        # 1. Create a Test User and Token
        user = User(email="sse_test_user@example.com", password_hash="hashed_pw", full_name="SSE User")
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(subject=str(user.id), role=user.role.value)
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Notebook and chat session
        notebook = Notebook(title="SSE Notebook", owner_id=user.id)
        db.add(notebook)
        db.commit()
        db.refresh(notebook)

        from app.models.notebook_chat import NotebookChatSession
        session = NotebookChatSession(notebook_id=notebook.id, user_id=user.id, title="SSE Chat Session")
        db.add(session)
        db.commit()
        db.refresh(session)

        # 3. Create completed asset for RAG context
        asset = Asset(
            notebook_id=notebook.id,
            file_name="sse_doc.pdf",
            file_path="notebooks/1/sse_doc.pdf",
            file_type="application/pdf",
            size=123,
            ingestion_status=AssetIngestionStatus.COMPLETED
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)

        from app.models.asset_embedding import AssetEmbedding
        chunk = AssetEmbedding(
            asset_id=asset.id,
            chunk_index=0,
            content="FastAPI is a modern, fast, high-performance web framework.",
            page_number=1
        )
        db.add(chunk)
        db.commit()

        client = TestClient(app)

        # =====================================================================
        # TEST 1: Normal Chat Flow with RAG
        # =====================================================================
        logger.info("--- TEST 1: Normal Chat Flow with RAG ---")
        
        # We need mock for condense_query_and_route returning needs_rag=True
        # We hack/mock generate_content_stream to yield some fake text chunks
        mock_response = MagicMock()
        mock_chunk_1 = MagicMock()
        mock_chunk_1.text = "FastAPI "
        mock_chunk_2 = MagicMock()
        mock_chunk_2.text = "is awesome [1]!"
        mock_response.__iter__.return_value = [mock_chunk_1, mock_chunk_2]
        
        with patch("app.services.notebook_chat_service.condense_query_and_route") as mock_condense, \
             patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls, \
             patch("app.services.retrieval_service.hybrid_retrieval") as mock_hybrid:
             
            mock_condense.return_value = {"needs_rag": True, "condensed_query": "What is FastAPI?"}
            mock_hybrid.return_value = {
                "status": "success",
                "context": "[1] [sse_doc.pdf:1] FastAPI is a modern, fast, high-performance web framework.",
                "chunks": [
                    {
                        "index": 1,
                        "file_name": "sse_doc.pdf",
                        "page_number": 1,
                        "asset_id": asset.id,
                        "content": "FastAPI is a modern, fast, high-performance web framework."
                    }
                ]
            }
            
            mock_genai_client = create_mock_genai_client()
            mock_client_cls.return_value = mock_genai_client
            mock_genai_client.models.generate_content_stream.return_value = mock_response
            mock_genai_client.models.generate_content.return_value.text = "Tiêu đề Học máy"
            
            url = f"/notebooks/{notebook.id}/sessions/{session.id}/chat"
            with client.stream("POST", url, json={"role": "user", "content": "What is FastAPI?"}, headers=headers) as res:
                assert res.status_code == 200
                events = []
                for line in res.iter_lines():
                    if line:
                        events.append(line)
            
            # Check event contents
            logger.info(f"Received SSE lines: {events}")
            
            # We expect event: citations, data: [...], event: delta, data: ..., event: done, data: ...
            assert any("event: citations" in e for e in events)
            assert any("FastAPI" in e for e in events)
            assert any("event: done" in e for e in events)

            # Assert exact SSE event sequence: citations -> delta -> done
            citation_idx = next(i for i, e in enumerate(events) if "event: citations" in e)
            delta_idx = next(i for i, e in enumerate(events) if "event: delta" in e)
            done_idx = next(i for i, e in enumerate(events) if "event: done" in e)
            assert citation_idx < delta_idx < done_idx

            # Check messages written to DB
            from app.models.notebook_chat import NotebookChatMessage
            db.expire_all()
            msgs = db.query(NotebookChatMessage).filter(NotebookChatMessage.session_id == session.id).order_by(NotebookChatMessage.created_at.asc()).all()
            assert len(msgs) == 2
            assert msgs[0].role == "user"
            assert msgs[0].content == "What is FastAPI?"
            assert msgs[1].role == "assistant"
            assert "FastAPI is awesome" in msgs[1].content
            
            # Assert citations details inside the DB message are properly parsed and pruned
            assert len(msgs[1].citations) == 1
            db_citation = msgs[1].citations[0]
            assert db_citation["file_name"] == "sse_doc.pdf"
            assert db_citation["page_number"] == 1
            assert db_citation["asset_id"] == asset.id
            assert "content" not in db_citation  # Verify block/content was pruned/removed
            assert "index" in db_citation
            
        logger.info("TEST 1 PASSED: SSE streamed RAG response and preserved message log!")

        # Clean messages
        db.query(NotebookChatMessage).delete()
        db.commit()

        # =====================================================================
        # TEST 2: General Chat / Chit-chat Flow (No RAG)
        # =====================================================================
        logger.info("--- TEST 2: General Chat / Chit-chat Flow (No RAG) ---")
        
        # Add a historical message to ensure is_first_turn evaluates to False
        # so that it executes the query condensation and intent routing logic.
        from app.models.notebook_chat import NotebookChatMessage
        historical_msg = NotebookChatMessage(session_id=session.id, role="user", content="Hi machine learning")
        db.add(historical_msg)
        db.commit()
        
        mock_response = MagicMock()
        mock_chunk_1 = MagicMock()
        mock_chunk_1.text = "Hello! "
        mock_chunk_2 = MagicMock()
        mock_chunk_2.text = "How can I help you?"
        mock_response.__iter__.return_value = [mock_chunk_1, mock_chunk_2]
        
        with patch("app.services.notebook_chat_service.condense_query_and_route") as mock_condense, \
             patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls, \
             patch("app.services.retrieval_service.hybrid_retrieval") as mock_hybrid:
             
            mock_condense.return_value = {"needs_rag": False, "condensed_query": "Hello."}
            mock_genai_client = create_mock_genai_client()
            mock_client_cls.return_value = mock_genai_client
            mock_genai_client.models.generate_content_stream.return_value = mock_response
            
            url = f"/notebooks/{notebook.id}/sessions/{session.id}/chat"
            res = client.post(url, json={"role": "user", "content": "Hello."}, headers=headers)
            
            assert res.status_code == 200
            # Since needs_rag=False, RAG retrieval MUST be bypassed
            mock_hybrid.assert_not_called()
            
            lines = res.content.decode("utf-8").split("\n")
            logger.info(f"Chit-chat SSE response lines: {lines}")
            assert any("Hello!" in line for line in lines)
            
        logger.info("TEST 2 PASSED: Chit-chat correctly routed without RAG.")

        # Clean messages
        db.query(NotebookChatMessage).delete()
        db.commit()

        # =====================================================================
        # TEST 3: Concurrency Guard (409 Conflict)
        # =====================================================================
        logger.info("--- TEST 3: Concurrency Guard (409 Conflict) ---")
        
        import httpx
        from fastapi import Request
        
        # We will dispatch two requests concurrently using AsyncClient
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            # We mock the Gemini stream to sleep/hold the generator execution to simulate long-running query
            async def streaming_generator(*args, **kwargs):
                yield "event: delta\ndata: \"starting\"\n\n"
                await asyncio.sleep(0.5)
                yield "event: done\ndata: {}\n\n"

            with patch("app.services.notebook_chat_service.stream_chat_response", side_effect=streaming_generator):
                url = f"/notebooks/{notebook.id}/sessions/{session.id}/chat"
                
                # Gather two concurrent requests!
                tasks = [
                    async_client.post(url, json={"role": "user", "content": "Hello 1"}, headers=headers),
                    async_client.post(url, json={"role": "user", "content": "Hello 2"}, headers=headers)
                ]
                
                res1, res2 = await asyncio.gather(*tasks)
                
                logger.info(f"Concurrent status codes: {res1.status_code}, {res2.status_code}")
                # One should be 200, the other should be 409
                status_codes = {res1.status_code, res2.status_code}
                assert 200 in status_codes
                assert 409 in status_codes
                
        logger.info("TEST 3 PASSED: Concurrency Guard successfully rejected simultaneous chat requests with 409.")

        # =====================================================================
        # TEST 4: Client Disconnect (Abrupt Termination & Gemini stream closure)
        # =====================================================================
        logger.info("--- TEST 4: Client Disconnect ---")
        
        # We will mock the Starlette Request to return True on is_disconnected()
        # and test the generator direct call and verify DB is NOT written.
        mock_request = MagicMock()
        async def mock_disconnected():
            return True
        mock_request.is_disconnected = mock_disconnected
        
        mock_gemini_stream = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.text = "Chunk 1"
        mock_gemini_stream.__iter__.return_value = [mock_chunk]
        
        # BackgroundTasks tracker
        bg_tasks = BackgroundTasksMock()
        
        with patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls, \
             patch("app.services.notebook_chat_service.condense_query_and_route") as mock_condense, \
             patch("app.services.retrieval_service.hybrid_retrieval") as mock_hybrid:
             
            mock_condense.return_value = {"needs_rag": False, "condensed_query": "hello limit"}
            mock_hybrid.return_value = {"status": "success", "context": "", "chunks": []}
            mock_genai_client = create_mock_genai_client()
            mock_client_cls.return_value = mock_genai_client
            mock_genai_client.models.generate_content_stream.return_value = mock_gemini_stream
            
            # Consume the async generator
            generator = stream_chat_response(
                db=db,
                notebook_id=notebook.id,
                session_id=session.id,
                user=user,
                raw_query="hello limit",
                request=mock_request,
                background_tasks=bg_tasks
            )
            
            outputs = []
            async for chunk in generator:
                outputs.append(chunk)

            logger.info(f"Disconnect output events: {outputs}")
            # Assert closed has been called on mock gemini stream
            mock_gemini_stream.close.assert_called_once()
            
            # DB messages should have 0 records since we aborted insert upon disconnect
            db.expire_all()
            msgs = db.query(NotebookChatMessage).filter(NotebookChatMessage.session_id == session.id).all()
            assert len(msgs) == 0
            
        logger.info("TEST 4 PASSED: Stream generator closed Gemini client response and skipped database commit upon client disconn.")

        # =====================================================================
        # TEST 5: Empty Notebook Fallback (Short-circuit & assert no Gemini call)
        # =====================================================================
        logger.info("--- TEST 5: Empty Notebook Fallback (Short-circuit verification) ---")
        
        # Create an empty notebook
        empty_notebook = Notebook(title="Empty SSE Notebook", owner_id=user.id)
        db.add(empty_notebook)
        db.commit()
        db.refresh(empty_notebook)
        
        empty_session = NotebookChatSession(notebook_id=empty_notebook.id, user_id=user.id, title="Empty SSE Session")
        db.add(empty_session)
        db.commit()
        db.refresh(empty_session)
        
        with patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls:
            mock_genai_client = create_mock_genai_client()
            mock_client_cls.return_value = mock_genai_client
            
            url = f"/notebooks/{empty_notebook.id}/sessions/{empty_session.id}/chat"
            res = client.post(url, json={"role": "user", "content": "Hỏi sách máy tính?"}, headers=headers)
            
            assert res.status_code == 200
            lines = res.content.decode("utf-8").split("\n")
            logger.info(f"Empty notebook SSE lines: {lines}")
            
            # Assert citations is empty
            assert any('data: []' in line for line in lines)
            # Assert fallback copy
            assert any("xin" in line and "trong" in line for line in lines)
            
            # MUST NOT HAVE CALLED GEMINI FOR GENERATING CONTENT
            mock_genai_client.models.generate_content_stream.assert_not_called()
            
            # Veriy that the messages WERE written to databases
            db.expire_all()
            msgs = db.query(NotebookChatMessage).filter(NotebookChatMessage.session_id == empty_session.id).order_by(NotebookChatMessage.created_at.asc()).all()
            assert len(msgs) == 2
            assert msgs[0].role == "user"
            assert msgs[1].role == "assistant"
            assert msgs[1].content == "Tôi xin lỗi, thông tin này không có trong tài liệu của bạn."
            
        logger.info("TEST 5 PASSED: Short-circuit empty notebooks correctly and bypassed LLM.")

        print("\nALL CHAT ORCHESTRATION & SSE STREAMING TESTS PASSED SUCCESSFULLY!")

    finally:
        logger.info("Database cleaning up test records...")
        db.refresh(user)
        db.delete(user)
        db.commit()
        db.close()
        logger.info("Cleanup done.")


class BackgroundTasksMock:
    def __init__(self):
        self.tasks = []
    def add_task(self, func, *args, **kwargs):
        self.tasks.append((func, args, kwargs))


if __name__ == "__main__":
    asyncio.run(run_tests())
