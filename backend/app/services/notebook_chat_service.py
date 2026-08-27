import logging
import asyncio
import re
import json
from google import genai
from google.genai import types
from fastapi import BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.models.notebook import Notebook
from app.models.notebook_chat import NotebookChatMessage, NotebookChatSession
from app.models.user import User
from app.schemas.notebook_chat import (
    NotebookChatMessageCreate,
    NotebookChatSessionCreate,
    NotebookChatSessionUpdate,
)

logger = logging.getLogger(__name__)


def validate_notebook_and_session(
    db: Session,
    notebook_id: int,
    user_id: int,
    session_id: int | None = None,
) -> NotebookChatSession | None:
    """
    Ownership Guard checking notebook existence, user ownership, and session ownership.
    Raises HTTP 404 if any check fails to prevent data exposure.
    """
    notebook = db.execute(
        select(Notebook).where(Notebook.id == notebook_id)
    ).scalar_one_or_none()
    
    if notebook is None or notebook.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )

    if session_id is not None:
        session = db.execute(
            select(NotebookChatSession).where(
                NotebookChatSession.id == session_id,
                NotebookChatSession.notebook_id == notebook_id,
                NotebookChatSession.user_id == user_id,
            )
        ).scalar_one_or_none()
        
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )
        return session
    return None


def create_chat_session(
    db: Session,
    notebook_id: int,
    user: User,
    data: NotebookChatSessionCreate,
) -> NotebookChatSession:
    """
    Creates a new chat session for a notebook.
    """
    validate_notebook_and_session(db, notebook_id, user.id)

    session = NotebookChatSession(
        notebook_id=notebook_id,
        user_id=user.id,
        title=data.title or "Phiên trò chuyện mới",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions_by_notebook(
    db: Session,
    notebook_id: int,
    user: User,
) -> list[NotebookChatSession]:
    """
    Retrieves all chat sessions of a notebook, ordered by updated_at descending.
    """
    validate_notebook_and_session(db, notebook_id, user.id)

    stmt = (
        select(NotebookChatSession)
        .where(
            NotebookChatSession.notebook_id == notebook_id,
            NotebookChatSession.user_id == user.id,
        )
        .order_by(NotebookChatSession.updated_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_session_messages(
    db: Session,
    notebook_id: int,
    session_id: int,
    user: User,
) -> list[NotebookChatMessage]:
    """
    Gets all messages in a session, in ascending created_at order.
    """
    validate_notebook_and_session(db, notebook_id, user.id, session_id)

    stmt = (
        select(NotebookChatMessage)
        .where(NotebookChatMessage.session_id == session_id)
        .order_by(NotebookChatMessage.created_at.asc(), NotebookChatMessage.id.asc())
    )
    return list(db.execute(stmt).scalars().all())


def rename_chat_session(
    db: Session,
    notebook_id: int,
    session_id: int,
    user: User,
    data: NotebookChatSessionUpdate,
) -> NotebookChatSession:
    """
    Updates the session title.
    """
    session = validate_notebook_and_session(db, notebook_id, user.id, session_id)
    assert session is not None

    session.title = data.title
    db.commit()
    db.refresh(session)
    return session


def delete_chat_session(
    db: Session,
    notebook_id: int,
    session_id: int,
    user: User,
) -> None:
    """
    Deletes the session, prompting cascades on messages.
    """
    session = validate_notebook_and_session(db, notebook_id, user.id, session_id)
    assert session is not None

    db.delete(session)
    db.commit()


def create_chat_message(
    db: Session,
    notebook_id: int,
    session_id: int,
    user: User,
    data: NotebookChatMessageCreate,
    background_tasks: BackgroundTasks,
) -> NotebookChatMessage:
    """
    Inserts a new message in a session. Bumps updated_at on the session.
    Triggers auto-titling if it's the very first message.

    TODO (Phase 4): This service method accepts arbitrary roles/citations from the client.
    Keep it open ONLY for Phase 1 testing/scaffolding. In Phase 4, we must either:
    1. Restrict client message input strictly to raw user content and only allow "user" role, OR
    2. De-couple direct message creations by clients and only allow SSE integration pipeline
       to insert assistant messages and reference citations.
    """
    session = validate_notebook_and_session(db, notebook_id, user.id, session_id)
    assert session is not None

    # Count existing messages inside the transaction to determine if first message
    messages_count = db.scalar(
        select(func.count(NotebookChatMessage.id)).where(
            NotebookChatMessage.session_id == session_id
        )
    ) or 0

    message = NotebookChatMessage(
        session_id=session_id,
        role=data.role,
        content=data.content,
        citations=data.citations,
        condensed_query=data.condensed_query,
    )
    db.add(message)

    # Bump updated_at of the session
    session.updated_at = func.now()
    db.commit()
    db.refresh(message)

    # Trigger auto-title if this is the first message overall (count was 0)
    if messages_count == 0:
        background_tasks.add_task(auto_title_session_task, session_id)

    return message


def auto_title_session_task(session_id: int) -> None:
    """
    Independent background task to automatically generate a title for the session
    based on its first message content using Gemini settings.GEMINI_CHAT_MODEL.
    """
    from app.core.database import SessionLocal
    
    logger.info(f"Triggering auto-titling background task for session_id={session_id}")
    db = SessionLocal()
    try:
        session = db.get(NotebookChatSession, session_id)
        if not session:
            logger.error(f"Auto-titling: Session {session_id} not found.")
            return

        # Fetch first message
        first_msg = db.execute(
            select(NotebookChatMessage)
            .where(NotebookChatMessage.session_id == session_id)
            .order_by(NotebookChatMessage.created_at.asc(), NotebookChatMessage.id.asc())
            .limit(1)
        ).scalar_one_or_none()

        if not first_msg or not first_msg.content:
            logger.warning(f"Auto-titling: Session {session_id} has no message content to summarize.")
            return

        # Prepare system prompt for Gemini
        prompt = (
            "Dựa trên tin nhắn đầu tiên sau của người dùng trong một cuộc hội thoại, "
            "hãy tạo ra một tiêu đề ngắn gọn, súc tích (dưới 5 từ) bằng tiếng Việt cho cuộc hội thoại này.\n"
            "Yêu cầu: Chỉ trả về tiêu đề thô, không kèm dấu ngoặc kép, không có chữ 'Tiêu đề:', không có markdown.\n\n"
            f"Tin nhắn: {first_msg.content}"
        )

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_CHAT_MODEL,
            contents=prompt,
        )

        raw_title = response.text or ""
        title = raw_title.strip().replace('"', '').replace("'", "")
        if len(title) > 100:
            title = title[:97] + "..."

        if not title:
            title = "Hội thoại mới"

        session.title = title
        db.commit()
        logger.info(f"Successfully auto-titled session {session_id} to '{title}'")
    except Exception as e:
        db.rollback()
        logger.exception(f"Error auto-titling session {session_id}: {e}")
    finally:
        db.close()


class CondensationResult(BaseModel):
    needs_rag: bool = Field(
        description="True if the query asks about document contents/knowledge and needs RAG, False for chit-chat, greetings, or metadata questions."
    )
    condensed_query: str = Field(
        description="The standalone rewritten query resolving references and pronouns to the conversation history. Strictly resolve references without adding any speculative keywords or replaying other facts."
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_gemini_condense(raw_query: str, history_text: str) -> CondensationResult:
    """
    Calls Gemini API to condense the query under tenacity retry.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    system_prompt = (
        "Bạn là một trợ lý RAG chuyên về phân tích ý định câu hỏi và rút gọn ngữ cảnh.\n"
        "Nhiệm vụ của bạn là đọc lịch sử hội thoại gần nhất và câu hỏi mới (raw query) của người dùng,\n"
        "sau đó xác định:\n"
        "1. `needs_rag` (bool): Câu hỏi mới có cần truy xuất kiến thức từ tài liệu (RAG) không. "
        "Đặt là True nếu câu hỏi hỏi về kiến thức chuyên môn, nội dung tài liệu. "
        "Đặt là False đối với các câu chào hỏi xã giao, cảm ơn, hỏi thăm thông thường, hoặc câu hỏi siêu dữ liệu không liên quan đến tài liệu học tập.\n"
        "2. `condensed_query` (str): Câu hỏi mới được viết lại độc lập (standalone), loại bỏ các tham chiếu đại từ (ví dụ: 'nó', 'chúng', 'cái đó', 'bước trước') "
        "bằng cách thay thế chúng bằng danh từ/ngữ cảnh chính xác thu được từ lịch sử hội thoại.\n"
        "CHỈ THỊ CỰC KỲ QUAN TRỌNG: Bạn chỉ được phân giải đại từ và ngữ cảnh. KHÔNG ĐƯỢC tự ý thêm từ khóa suy đoán, giải nghĩa hay phát biểu lại câu hỏi ở định dạng khác. "
        "Nếu câu hỏi mới đã đầy đủ nghĩa và không cần phân giải ngữ cảnh, hãy giữ nguyên câu hỏi mới đó làm `condensed_query`."
    )
    
    prompt = (
        f"Lịch sử hội thoại gần đây:\n{history_text}\n"
        f"Câu hỏi mới của người dùng: {raw_query}\n"
    )
    
    response = client.models.generate_content(
        model=settings.GEMINI_CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=CondensationResult,
        ),
    )
    
    import json
    data = json.loads(response.text)
    return CondensationResult(**data)


def condense_query_and_route(history: list[NotebookChatMessage], raw_query: str) -> dict:
    """
    Condenses raw_query against a sliding window (max 6 messages) of chat history,
    and routes intent to decide if RAG retrieval is required.
    """
    # Sliding window: max 6 recent messages
    recent_history = history[-6:] if history else []
    history_text = ""
    for msg in recent_history:
        role_label = "User" if msg.role == "user" else "Assistant"
        history_text += f"{role_label}: {msg.content}\n"

    try:
        # For first turn, history_text is empty, but we still query Gemini to verify the needs_rag classification
        result = _call_gemini_condense(raw_query, history_text)
        logger.info(f"Classification successful: needs_rag={result.needs_rag}, condensed='{result.condensed_query}'")
        return {
            "needs_rag": result.needs_rag,
            "condensed_query": raw_query if not history else result.condensed_query,
        }
    except Exception as e:
        logger.warning(
            f"Classification/Condensation failed after retries: {e}. Running fallback checks.",
            exc_info=True,
        )
        words = raw_query.strip().split()
        needs_rag = False if len(words) <= 3 else True
        return {
            "needs_rag": needs_rag,
            "condensed_query": raw_query,
        }


_session_locks: dict[int, asyncio.Lock] = {}


def get_session_lock(session_id: int) -> asyncio.Lock:
    """
    Returns an in-memory asyncio Lock specific to the session_id to guard concurrency.
    """
    if session_id not in _session_locks:
        _session_locks[session_id] = asyncio.Lock()
    return _session_locks[session_id]


async def stream_chat_response(
    db: Session,
    notebook_id: int,
    session_id: int,
    user: User,
    raw_query: str,
    request,
    background_tasks: BackgroundTasks,
):
    """
    Orchestrates the query condensation, scoped retrieval, Gemini text streaming,
    citations clean-up, and write-on-complete message persistence.
    """
    try:
        # 1. First-turn computation
        message_count = db.scalar(
            select(func.count(NotebookChatMessage.id)).where(
                NotebookChatMessage.session_id == session_id
            )
        ) or 0
        is_first_turn = (message_count == 0)

        # 2. Get history and condense/intent route
        history = [] if is_first_turn else get_session_messages(db, notebook_id, session_id, user)
        condense_res = condense_query_and_route(history, raw_query)
        needs_rag = condense_res["needs_rag"]
        condensed_query = condense_res["condensed_query"]

        citations = []
        context_str = ""
        short_circuit = False

        # 3. Retrieve context if needs_rag
        if needs_rag:
            from app.services.retrieval_service import hybrid_retrieval
            retrieval_res = hybrid_retrieval(db, notebook_id, condensed_query)
            if retrieval_res.get("status") == "no_documents":
                short_circuit = True
            else:
                chunks = retrieval_res.get("chunks", [])
                context_str = retrieval_res.get("context", "")
                citations = [
                    {
                        "index": c["index"],
                        "file_name": c["file_name"],
                        "page_number": c["page_number"],
                        "asset_id": c["asset_id"],
                    }
                    for c in chunks
                ]

        # 4. Stream citations event immediately
        yield f"event: citations\ndata: {json.dumps(citations)}\n\n"

        assistant_reply = ""

        # 5. Handle response generation
        if short_circuit:
            logger.info("Chat stream: no documents. Short-circuiting with standard refusal.")
            assistant_reply = "Tôi xin lỗi, thông tin này không có trong tài liệu của bạn."
            yield f"event: delta\ndata: {json.dumps(assistant_reply)}\n\n"
        else:
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            if needs_rag:
                system_instruction = (
                    "Bạn là một trợ lý RAG thông minh.\n"
                    "Hãy trả lời câu hỏi của người dùng bằng tiếng Việt, DỰA TRÊN NGỮ CẢNH tài liệu dưới đây.\n"
                    "Yêu cầu chung:\n"
                    "1. Trả lời rõ ràng, mạch lạc, trực tiếp.\n"
                    "2. Sử dụng định dạng trích dẫn đánh số [1], [2]... để dẫn nguồn trực tiếp từ các đoạn văn bản tương ứng trong context.\n"
                    "3. Nếu thông tin không có trong tài liệu/ngữ cảnh dưới đây, hãy trả lời đúng nguyên văn câu sau: "
                    "'Tôi xin lỗi, thông tin này không có trong tài liệu của bạn.' và TRÁNH tự bịa đặt hay sử dụng kiến thức ngoài.\n\n"
                    f"Ngữ cảnh tài liệu:\n{context_str}"
                )
            else:
                system_instruction = (
                    "Bạn là một trợ lý thông minh.\n"
                    "Hãy trò chuyện xã giao, trả lời câu hỏi tổng quát bằng tiếng Việt một cách tự nhiên và lịch sự."
                )

            contents = []
            if not is_first_turn:
                # Retrieve history and append in types.Content list format
                recent_history = history[-6:]
                for msg in recent_history:
                    role_name = "user" if msg.role == "user" else "model"
                    contents.append(
                        types.Content(
                            role=role_name,
                            parts=[types.Part.from_text(text=msg.content)]
                        )
                    )
            # Add current user message
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=raw_query)]
                )
            )

            # Stream from Gemini
            response_stream = None
            try:
                response_stream = client.models.generate_content_stream(
                    model=settings.GEMINI_CHAT_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    ),
                )
                
                for chunk in response_stream:
                    if await request.is_disconnected():
                        logger.info("Client disconnected. Breaking Gemini stream.")
                        break
                    
                    text_chunk = chunk.text or ""
                    if text_chunk:
                        assistant_reply += text_chunk
                        yield f"event: delta\ndata: {json.dumps(text_chunk)}\n\n"
                        
            except Exception as e:
                logger.error(f"Error streaming from Gemini: {e}", exc_info=True)
                yield f"event: error\ndata: {json.dumps({'message': 'Có lỗi xảy ra khi xử lý phản hồi từ Gemini.'})}\n\n"
                return
            finally:
                if response_stream is not None:
                    if hasattr(response_stream, "close") and callable(getattr(response_stream, "close")):
                        try:
                            response_stream.close()
                        except Exception:
                            pass

        # 6. Check client disconnection before database write
        if await request.is_disconnected():
            logger.info("Client disconnected before saving messages. Aborting save.")
            return

        # 7. Write-on-complete: insert user + assistant messages in a single transaction
        used_indices = set(int(x) for x in re.findall(r"\[(\d+)\]", assistant_reply))
        cleaned_citations = [
            c for c in citations if c["index"] in used_indices
        ]

        user_msg = NotebookChatMessage(
            session_id=session_id,
            role="user",
            content=raw_query,
            condensed_query=condensed_query,
        )
        db.add(user_msg)

        ass_msg = NotebookChatMessage(
            session_id=session_id,
            role="assistant",
            content=assistant_reply,
            citations=cleaned_citations,
        )
        db.add(ass_msg)

        # Update session
        session = db.get(NotebookChatSession, session_id)
        if session:
            session.updated_at = func.now()

        db.commit()
        db.refresh(user_msg)
        db.refresh(ass_msg)

        # 8. Trigger auto-title if first turn
        if is_first_turn:
            background_tasks.add_task(auto_title_session_task, session_id)

        # 9. Yield done event
        done_payload = {
            "session_id": session_id,
            "message_id": ass_msg.id,
            "condensed_query": condensed_query,
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

    except Exception as e:
        logger.exception("Error during streaming chat orchestration")
        yield f"event: error\ndata: {json.dumps({'message': 'Có lỗi hệ thống xảy ra.'})}\n\n"
