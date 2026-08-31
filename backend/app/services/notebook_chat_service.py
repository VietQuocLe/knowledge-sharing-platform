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
from app.core.observability import observe_llm, update_trace_context
from app.models.enums import ChatMessageRole
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


@observe_llm(name="condense_query")
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
        role_label = "User" if msg.role == ChatMessageRole.USER else "Assistant"
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


@observe_llm(name="notebook_rag_chat_stream")
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
    citations clean-up, token tracking, and write-on-complete message persistence.
    """
    update_trace_context(
        user_id=str(user.id),
        session_id=str(session_id),
        tags=["rag-chat", f"notebook-{notebook_id}"],
    )
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
        prompt_tokens: int | None = None
        completion_tokens: int | None = None

        # 5. Handle response generation
        if short_circuit:
            logger.info("Chat stream: no documents. Short-circuiting with standard refusal.")
            assistant_reply = "Tôi xin lỗi, thông tin này không có trong tài liệu của bạn."
            yield f"event: delta\ndata: {json.dumps(assistant_reply)}\n\n"
        else:
            client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            
            if needs_rag:
                system_instruction = (
                    "Bạn là một trợ giảng / cố vấn học tập thông thái, nhiệt tình và rõ ràng (chuẩn NotebookLM & Studocu).\n"
                    "Nhiệm vụ của bạn là giải thích kiến thức và trả lời câu hỏi của người học bằng tiếng Việt, DỰA TRÊN NGỮ CẢNH tài liệu dưới đây.\n\n"
                    "QUY TẮC PHẢN HỒI & PHONG CÁCH DIỄN ĐẠT:\n"
                    "1. Vai trò & Giọng văn (Tone & Persona):\n"
                    "   - Xưng hô tự nhiên, lịch thiệp ('tôi' - 'bạn'). Giải thích sâu sắc, dễ hiểu, trực diện vào trọng tâm câu hỏi trước, sau đó phân tích chi tiết kèm ví dụ minh họa hoặc công thức rõ ràng.\n"
                    "   - Tránh tuyệt đối các từ ngữ máy móc, sáo rỗng hoặc mở đầu rập khuôn như: 'Dựa vào tài liệu được cung cấp...', 'Theo như trang X trong slide...', 'Như trong context đã nêu...'. Hãy trình bày tri thức một cách tự nhiên và mạch lạc.\n"
                    "2. Quy tắc Trích dẫn Nguồn (Citation Standard):\n"
                    "   - Đặt nhãn trích dẫn số trong ngoặc vuông như [1], [2] ngay sau từng câu/luận điểm có căn cứ từ tài liệu nguồn tương ứng.\n"
                    "3. Định dạng Markdown Thẩm mỹ:\n"
                    "   - Dùng **in đậm** các từ khóa/khái niệm cốt lõi để người học dễ nắm bắt (scannable reading).\n"
                    "   - Phân chia các đoạn văn ngắn gọn, sử dụng bullet points (-), bảng biểu so sánh hoặc khối code/công thức toán ($...$ hoặc $$...$$) khi thích hợp.\n"
                    "4. Xử lý câu hỏi ngoài phạm vi tài liệu (Anti-Hallucination Guard):\n"
                    "   - Nếu thông tin hoàn toàn không có trong tài liệu/ngữ cảnh dưới đây, hãy trả lời đúng nguyên văn câu sau: "
                    "'Tôi xin lỗi, thông tin này không có trong tài liệu của bạn.' và TRÁNH tự bịa đặt hay sử dụng kiến thức ngoài.\n\n"
                    f"Ngữ cảnh tài liệu:\n{context_str}"
                )
            else:
                system_instruction = (
                    "Bạn là một trợ giảng / cố vấn học tập thông minh, thân thiện và nhiệt tình.\n"
                    "Hãy trò chuyện xã giao, trả lời câu hỏi tổng quát bằng tiếng Việt một cách tự nhiên, lịch thiệp ('tôi' - 'bạn') và mạch lạc."
                )

            contents = []
            if not is_first_turn:
                # Retrieve history and append in types.Content list format
                recent_history = history[-6:]
                for msg in recent_history:
                    role_name = "user" if msg.role == ChatMessageRole.USER else "model"
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
                    
                    if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                        um = chunk.usage_metadata
                        p_cnt = getattr(um, "prompt_token_count", None)
                        if isinstance(p_cnt, int):
                            prompt_tokens = p_cnt
                        c_cnt = getattr(um, "candidates_token_count", None)
                        if isinstance(c_cnt, int):
                            completion_tokens = c_cnt
                    
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

        # 6. Write-on-complete: insert user + assistant messages in a single transaction
        used_indices = set(int(x) for x in re.findall(r"\[(\d+)\]", assistant_reply))
        cleaned_citations = [
            c for c in citations if c["index"] in used_indices
        ]

        user_msg = NotebookChatMessage(
            session_id=session_id,
            role=ChatMessageRole.USER,
            content=raw_query,
            condensed_query=condensed_query,
        )
        db.add(user_msg)

        ass_msg = NotebookChatMessage(
            session_id=session_id,
            role=ChatMessageRole.ASSISTANT,
            content=assistant_reply,
            citations=cleaned_citations,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        db.add(ass_msg)

        # Update session
        session = db.get(NotebookChatSession, session_id)
        if session:
            session.updated_at = func.now()

        db.commit()
        db.refresh(user_msg)
        db.refresh(ass_msg)

        # 7. Trigger auto-title if first turn
        if is_first_turn:
            background_tasks.add_task(auto_title_session_task, session_id)

        # 8. Yield done event with full token usage details (if client still connected)
        try:
            total_tokens = (
                (prompt_tokens or 0) + (completion_tokens or 0)
                if (prompt_tokens is not None or completion_tokens is not None)
                else None
            )
            done_payload = {
                "session_id": session_id,
                "message_id": ass_msg.id,
                "condensed_query": condensed_query,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
            if not await request.is_disconnected():
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
        except Exception as e:
            logger.debug(f"Could not send done event to client: {e}")

    except Exception as e:
        logger.exception("Error during streaming chat orchestration")
        yield f"event: error\ndata: {json.dumps({'message': 'Có lỗi hệ thống xảy ra.'})}\n\n"
