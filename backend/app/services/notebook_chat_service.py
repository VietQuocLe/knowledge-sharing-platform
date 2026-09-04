"""
Proxy re-export module for backward compatibility.
Original implementation has been migrated to app.rag.chat.service.
"""
from google import genai  # noqa: F401
from app.rag.chat.service import (
    validate_notebook_and_session,
    create_chat_session,
    list_sessions_by_notebook,
    get_session_messages,
    rename_chat_session,
    delete_chat_session,
    create_chat_message,
    auto_title_session_task,
    CondensationResult,
    _call_gemini_condense,
    condense_query_and_route,
    _session_locks,
    get_session_lock,
    stream_chat_response,
)
from app.rag.chat.service import *  # noqa: F401, F403
