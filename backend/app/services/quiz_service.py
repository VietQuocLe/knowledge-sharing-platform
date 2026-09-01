import logging
from typing import List
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.observability import observe_llm
from app.models.asset import Asset
from app.models.asset_embedding import AssetEmbedding
from app.schemas.artifact import QuizContentPayload, QuizGenerateRequest
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def linear_space_sampling(chunks: List[AssetEmbedding], budget_per_asset: int) -> List[AssetEmbedding]:
    """
    Applies the Multi-Asset Linear Space Sampling algorithm to a list of chunks from a single asset.
    """
    total_chunks = len(chunks)
    if total_chunks <= budget_per_asset:
        return chunks

    if budget_per_asset == 1:
        return [chunks[0]]

    sampled = []
    for i in range(budget_per_asset):
        index = round(i * (total_chunks - 1) / (budget_per_asset - 1))
        sampled.append(chunks[index])
    return sampled


def extract_context_from_assets(db: Session, selected_asset_ids: List[int]) -> str:
    """
    Queries chunks joining AssetEmbedding and Asset, applies linear space sampling,
    and returns format-bonded context string.
    """
    # 1. Query JOIN AssetEmbedding and Asset (to get file_name) ordered by: asset_id, page_number ASC, chunk_index ASC
    stmt = (
        select(AssetEmbedding, Asset.file_name)
        .join(Asset, AssetEmbedding.asset_id == Asset.id)
        .where(AssetEmbedding.asset_id.in_(selected_asset_ids))
        .order_by(
            AssetEmbedding.asset_id,
            AssetEmbedding.page_number.asc(),
            AssetEmbedding.chunk_index.asc(),
        )
    )
    result = db.execute(stmt).all()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không tìm thấy nội dung văn bản hợp lệ để tạo bài tập",
        )

    # Group embedding rows by asset_id
    from collections import defaultdict
    asset_groups = defaultdict(list)
    for row in result:
        embedding = row.AssetEmbedding
        # Attach file_name dynamically to embedding object for formatting later
        embedding.asset_file_name = row.file_name
        asset_groups[embedding.asset_id].append(embedding)

    # 2. Multi-Asset Linear Space Sampling
    total_budget = settings.QUIZ_GENERATION_CHUNK_BUDGET
    budget_per_asset = max(1, total_budget // len(selected_asset_ids))

    selected_chunks = []
    # Make sure we process asset_ids in deterministic order (sorted)
    for asset_id in sorted(asset_groups.keys()):
        asset_chunks = asset_groups[asset_id]
        sampled_asset_chunks = linear_space_sampling(asset_chunks, budget_per_asset)
        selected_chunks.extend(sampled_asset_chunks)

    # Cap total selected chunks at total_budget just in case
    selected_chunks = selected_chunks[:total_budget]

    # 3. Format Context
    context_text = ""
    for chunk in selected_chunks:
        context_text += f"[Tài liệu: {getattr(chunk, 'asset_file_name', 'Tài liệu không rõ')} - Trang {chunk.page_number}]\n{chunk.content}\n\n"

    return context_text


@observe_llm(name="generate_quiz")
@retry(
    stop=stop_after_attempt(settings.GEMINI_QUIZ_RETRY_ATTEMPTS),
    wait=wait_exponential(
        multiplier=settings.GEMINI_QUIZ_RETRY_MULTIPLIER,
        min=settings.GEMINI_QUIZ_RETRY_MIN_WAIT,
        max=settings.GEMINI_QUIZ_RETRY_MAX_WAIT,
    ),
    reraise=True,
)
def _call_gemini_with_retry(context_text: str, num_questions: int) -> QuizContentPayload:
    """
    Stateless pure function that requests structured quiz output from Gemini 3.1-flash-lite.
    Handles API validations/API errors with tenacity retry.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    system_instruction = (
        "Bạn là một chuyên gia khảo thí và thiết kế học liệu chuẩn quốc tế (Studocu & NotebookLM standard).\n"
        f"Nhiệm vụ của bạn là sinh ra đúng chính xác {num_questions} câu hỏi trắc nghiệm khách quan 4 lựa chọn từ ngữ cảnh tài liệu được cung cấp.\n\n"
        "YÊU CẦU THIẾT KẾ ĐỀ THI & PHÂN BỔ NỘI DUNG:\n"
        "1. Phân bổ Bloom Taxonomy:\n"
        "   - 30% câu hỏi ở mức Nhận biết / Thông hiểu (nhận diện định nghĩa, phân biệt khái niệm cốt lõi, so sánh trực tiếp).\n"
        "   - 70% câu hỏi ở mức Vận dụng / Tình huống / Suy luận logic (áp dụng lý thuyết vào tình huống thực tế, biến đổi giải bài toán, suy luận từ dữ kiện ngầm định).\n"
        "2. An toàn dữ liệu & Chống bịa đặt (Anti-Hallucination):\n"
        "   - Tất cả câu hỏi, phương án lựa chọn và lời giải thích phải hoàn toàn dựa trên và suy luận chặt chẽ từ ngữ cảnh được cung cấp. Tuyệt đối không tự bịa đặt hay sử dụng tri thức ngoài ngữ cảnh.\n"
        "   - Nếu ngữ cảnh ngắn hoặc hẹp, hãy triệt để khai thác đọc hiểu ngữ nghĩa và suy luận logic từ dữ kiện có sẵn thay vì báo lỗi.\n"
        "3. Tiêu chuẩn Thiết kế Phương án (A, B, C, D):\n"
        "   - Luôn cung cấp đúng 4 phương án lựa chọn có key lần lượt là A, B, C, D.\n"
        "   - Cấm tuyệt đối các phương án lười biếng như: 'Tất cả các đáp án trên đều đúng', 'Cả A và B đều đúng', 'Không có đáp án nào đúng', hoặc các câu từ tương tự.\n"
        "   - Các phương án phải có cấu trúc tương đương và độ dài tương đối đồng đều nhằm đảm bảo tính nhiễu sư phạm tốt.\n"
        "4. Tiêu chuẩn Thiết kế Lời giải thích (Explanation Standard - Chuẩn Studocu / NotebookLM):\n"
        "   - Lời giải thích phải là một bài giảng giải chi tiết, hoàn chỉnh và tự thân có nghĩa (self-contained reasoning), giúp người học hiểu thấu đáo bản chất bài toán mà không cần mở lại slide.\n"
        "   - Cấu trúc lời giải thích gồm 3 phần rõ ràng:\n"
        "     * Bản chất lý thuyết: Nêu ngắn gọn nguyên lý, định nghĩa hoặc công thức được áp dụng.\n"
        "     * Suy luận / Giải bài toán từng bước (Step-by-step Derivation): Trình bày tường minh các bước biến đổi, thế số, suy luận logic dẫn tới kết quả đúng.\n"
        "     * Phân tích loại trừ: Giải thích ngắn gọn vì sao các phương án gây nhiễu còn lại là sai hoặc chưa chính xác.\n"
        "   - Cấm tuyệt đối cách giải thích lười biếng như: 'Theo tài liệu trang 15 có nói...', 'Đáp án A đúng vì câu hỏi hỏi về A...'.\n"
    )

    prompt = (
        f"Ngữ cảnh tài liệu học tập:\n"
        f"-------------------\n"
        f"{context_text}\n"
        f"-------------------\n\n"
        f"Hãy sinh chính xác {num_questions} câu hỏi dựa trên các yêu cầu hệ thống ở trên."
    )

    response = client.models.generate_content(
        model=settings.GEMINI_CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=QuizContentPayload,
        ),
    )

    if not response.text:
        raise ValueError("Nhận được phản hồi trống từ Gemini API")

    import json
    data = json.loads(response.text)
    return QuizContentPayload(**data)
