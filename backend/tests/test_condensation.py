import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Set environment overrides to connect locally (outside Docker) if not set
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5433")
os.environ.setdefault("MINIO_HOST", "localhost")

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.models.notebook_chat import NotebookChatMessage
from app.services.notebook_chat_service import condense_query_and_route

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_condensation")


def run_tests():
    # ==========================================
    # TEST 1: First-turn (Empty history)
    # ==========================================
    logger.info("--- TEST 1: First-turn (Empty history) ---")
    
    # We pass empty history
    history = []
    
    # Now it queries Gemini to determine needs_rag, rather than bypassing.
    with patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.text = '{"needs_rag": true, "condensed_query": "Mạng nơ-ron hoạt động ra sao?"}'
        mock_client.models.generate_content.return_value = mock_resp

        result = condense_query_and_route(history, "Mạng nơ-ron hoạt động ra sao?")
        
        assert result["needs_rag"] is True
        assert result["condensed_query"] == "Mạng nơ-ron hoạt động ra sao?"
        mock_client.models.generate_content.assert_called_once()
        
    logger.info("TEST 1 PASSED: First-turn query processed and classified via Gemini correctly.")

    # ==========================================
    # TEST 2: Pronoun Resolution
    # ==========================================
    logger.info("--- TEST 2: Pronoun Resolution ---")
    
    # Make a mock history
    msg_user = NotebookChatMessage(role="user", content="Mạng nơ-ron CNN hoạt động như thế nào?")
    msg_assistant = NotebookChatMessage(role="assistant", content="CNN kết hợp tích chập và pooling để trích xuất đặc trưng.")
    history = [msg_user, msg_assistant]
    
    raw_query = "Nó dùng để làm gì?"
    
    # Mock Gemini client call
    with patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.text = '{"needs_rag": true, "condensed_query": "Mạng nơ-ron CNN dùng để làm gì?"}'
        mock_client.models.generate_content.return_value = mock_resp
        
        result = condense_query_and_route(history, raw_query)
        
        assert result["needs_rag"] is True
        assert result["condensed_query"] == "Mạng nơ-ron CNN dùng để làm gì?"
        
        # Verify it was called with correct model from settings
        mock_client.models.generate_content.assert_called_once()
        logger.info(f"TEST 2 PASSED: Rewritten condensed query: '{result['condensed_query']}'")

    # ==========================================
    # TEST 3: Chit-chat / Routing
    # ==========================================
    logger.info("--- TEST 3: Chit-chat / Routing ---")
    
    history = [msg_user, msg_assistant]
    raw_query = "Cảm ơn bạn nhiều nhé!"
    
    with patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.text = '{"needs_rag": false, "condensed_query": "Cảm ơn bạn nhiều nhé!"}'
        mock_client.models.generate_content.return_value = mock_resp
        
        result = condense_query_and_route(history, raw_query)
        
        assert result["needs_rag"] is False
        assert result["condensed_query"] == "Cảm ơn bạn nhiều nhé!"
        
    logger.info("TEST 3 PASSED: Chit-chat correctly routed without RAG.")

    # ==========================================
    # TEST 4: Retry & Fallback on Gemini Error
    # ==========================================
    logger.info("--- TEST 4: Retry & Fallback on Gemini Error ---")
    
    history = [msg_user, msg_assistant]
    raw_query = "Câu hỏi lỗi."  # 3 words -> needs_rag = False
    
    # We patch time.sleep to avoid waiting 14 seconds during retries
    with patch("time.sleep") as mock_sleep, \
         patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls:
          
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        # Make the LLM call fail every time to trigger retries and fallback
        mock_client.models.generate_content.side_effect = Exception("Google API Quota Limit Exceeded")
        
        result = condense_query_and_route(history, raw_query)
        
        # Fallback values for short queries (<= 3 words)
        assert result["needs_rag"] is False
        assert result["condensed_query"] == raw_query
        
        # Verify generate_content called exactly 3 times (due to stop_after_attempt(3))
        assert mock_client.models.generate_content.call_count == 3
        # Verify sleep was called to wait between retries
        assert mock_sleep.call_count == 2
        
    # Also verify fallback with a long query (> 3 words) -> needs_rag = True
    with patch("time.sleep") as mock_sleep, \
         patch("app.services.notebook_chat_service.genai.Client") as mock_client_cls:
          
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("Google API Quota Limit Exceeded")
        
        long_query = "Mạng nơ-ron nhân tạo hoạt động thế nào hả bạn?"
        result_long = condense_query_and_route(history, long_query)
        
        # Fallback values for long queries (> 3 words)
        assert result_long["needs_rag"] is True
        assert result_long["condensed_query"] == long_query

    logger.info("TEST 4 PASSED: Fallback triggers <=3 word count check and defaults needs_rag appropriately.")

    print("\nALL INTENT ROUTING & QUERY CONDENSATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_tests()
