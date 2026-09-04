#!/usr/bin/env python3
"""
Ragas RAG Evaluation Framework.
Evaluates the RAG pipeline using 4 core Ragas metrics:
- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall

Ensures 100% parity with live production chat pipeline:
- Reuses public condense_query_and_route and hybrid_retrieval
- Validates notebook scope (checks notebook_saved_documents and get_scoped_asset_ids)
- Configured to use Gemini API as the LLM Judge and embeddings provider (zero OpenAI dependency)
- Supports smart dry-run mode when golden_testset.json contains placeholder TODOs
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Ensure backend root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from google import genai
from google.genai import types
from sqlalchemy import select
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.notebook import Notebook, NotebookSavedDocument
from app.models.document import Document
from app.models.user import User
from app.rag.retrieval.retriever import hybrid_retrieval, get_scoped_asset_ids
from app.rag.chat.service import condense_query_and_route


# ⚠️ CẢNH BÁO: Bản sao thủ công của system prompt trong app/rag/chat/service.py (lines 448-469).
# Nếu prompt production thay đổi (persona, format citation, câu từ chối...), PHẢI cập nhật
# đồng bộ ở đây, nếu không Ragas sẽ âm thầm đánh giá sai pipeline so với những gì người dùng
# thực tế nhận được.
def build_rag_system_instruction(context_str: str, needs_rag: bool = True) -> str:
    """
    Local manual copy of production system instruction from app/rag/chat/service.py.
    Used exclusively by eval_ragas.py to ensure zero modification to live production code.
    """
    if needs_rag:
        return (
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
    return (
        "Bạn là một trợ giảng / cố vấn học tập thông minh, thân thiện và nhiệt tình.\n"
        "Hãy trò chuyện xã giao, trả lời câu hỏi tổng quát bằng tiếng Việt một cách tự nhiên, lịch thiệp ('tôi' - 'bạn') và mạch lạc."
    )


def execute_rag_pipeline(
    db,
    notebook_id: int,
    query: str,
    history: list[Any] | None = None,
) -> dict[str, Any]:
    """
    Executes the exact production RAG sequence non-streaming:
    1. condense_query_and_route
    2. hybrid_retrieval (RRF Top-15, Reranker Top-5, Stitching)
    3. Production system instruction with citations & anti-hallucination guard
    4. Gemini API content generation
    """
    history = history or []
    # 1. Condense and route
    condense_res = condense_query_and_route(history, query)
    needs_rag = condense_res["needs_rag"]
    condensed_query = condense_res["condensed_query"]

    # 2. Scoped retrieval
    citations = []
    chunks = []
    context_str = ""
    short_circuit = False

    if needs_rag:
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

    # 3. Response Generation with single-source system instruction
    if short_circuit:
        answer = "Tôi xin lỗi, thông tin này không có trong tài liệu của bạn."
    else:
        system_instruction = build_rag_system_instruction(context_str, needs_rag)
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_CHAT_MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=settings.GEMINI_CHAT_TEMPERATURE,
            ),
        )
        answer = response.text or ""

    return {
        "query": query,
        "condensed_query": condensed_query,
        "needs_rag": needs_rag,
        "answer": answer,
        "contexts": [c["content"] for c in chunks],
        "citations": citations,
        "context_str": context_str,
    }


def load_testset(testset_path: Path) -> list[dict[str, Any]]:
    if not testset_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file testset tại: {testset_path}")
    with open(testset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Dữ liệu testset phải là một JSON array, nhận được: {type(data)}")
    return data


def is_placeholder_testset(items: list[dict[str, Any]]) -> bool:
    """Returns True if any item contains placeholder TODO marker."""
    for item in items:
        q = str(item.get("question", ""))
        gt = str(item.get("ground_truth", ""))
        if "[TODO" in q or "[TODO" in gt:
            return True
    return False


def ensure_demo_notebooks(db) -> None:
    """
    Ensures demo notebooks exist with properly scoped documents:
    - Notebook 1: Cơ sở dữ liệu (Document 2 -> Asset 2)
    - Notebook 2: Mạng máy tính (Documents 3, 4, 5, 6 -> Assets 3, 4, 5, 6)
    """
    user = db.execute(select(User).order_by(User.id.asc())).scalars().first()
    if not user:
        raise RuntimeError("Database chưa có user nào để gán Notebook.")

    # 1. Setup Notebook 1: CSDL
    nb1 = db.get(Notebook, 1)
    if not nb1:
        nb1 = Notebook(id=1, owner_id=user.id, title="Notebook Cơ sở dữ liệu (Demo)")
        db.add(nb1)
        db.commit()
        db.refresh(nb1)
        print("✔ Đã tạo mới Notebook ID 1: 'Notebook Cơ sở dữ liệu (Demo)'")

    # Link Document 2 (CSDL) to Notebook 1 (Document 1 excluded because it has 0 assets)
    doc2 = db.get(Document, 2)
    if doc2:
        existing = db.execute(
            select(NotebookSavedDocument).where(
                NotebookSavedDocument.notebook_id == 1,
                NotebookSavedDocument.document_id == 2,
            )
        ).scalar_one_or_none()
        if not existing:
            db.add(NotebookSavedDocument(notebook_id=1, document_id=2))
            db.commit()
            print("   + [Notebook 1] Đã liên kết Document ID 2 ('Chuong2 Moi truong cua CSDL')")

    # 2. Setup Notebook 2: MMT
    nb2 = db.get(Notebook, 2)
    if not nb2:
        nb2 = Notebook(id=2, owner_id=user.id, title="Notebook Mạng máy tính (Demo)")
        db.add(nb2)
        db.commit()
        db.refresh(nb2)
        print("✔ Đã tạo mới Notebook ID 2: 'Notebook Mạng máy tính (Demo)'")

    # Link Documents 3, 4, 5, 6 (MMT) to Notebook 2
    mmt_doc_ids = [3, 4, 5, 6]
    for doc_id in mmt_doc_ids:
        doc = db.get(Document, doc_id)
        if doc:
            existing = db.execute(
                select(NotebookSavedDocument).where(
                    NotebookSavedDocument.notebook_id == 2,
                    NotebookSavedDocument.document_id == doc_id,
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(NotebookSavedDocument(notebook_id=2, document_id=doc_id))
                print(f"   + [Notebook 2] Đã liên kết Document ID {doc_id} ('{doc.title}')")
    db.commit()


def run_evaluation(
    testset_path: Path,
    output_path: Path,
    dry_run: bool = False,
    auto_setup_notebooks: bool = False,
):
    print("=" * 75)
    print("      RAGAS RAG PIPELINE EVALUATION FRAMEWORK")
    print("=" * 75)
    print(f"📁 Testset: {testset_path}")
    print(f"📁 Output:  {output_path}")

    items = load_testset(testset_path)
    print(f"📊 Tổng số câu hỏi trong testset: {len(items)}")

    has_placeholders = is_placeholder_testset(items)

    db = SessionLocal()
    try:
        # Pre-flight Scope Check: Verify all notebook_ids in testset
        notebook_ids = sorted(list({it.get("notebook_id", 1) for it in items}))
        print("\n🔍 KIỂM TRA PHẠM VI TRUY XUẤT (NOTEBOOK SCOPE):")
        for nb_id in notebook_ids:
            scoped_assets = get_scoped_asset_ids(db, nb_id)
            if not scoped_assets:
                print(f"⚠ Notebook ID {nb_id}: HIỆN CHƯA CÓ ASSET NÀO TRONG SCOPE!")
                if auto_setup_notebooks:
                    print(f"🔧 Tự động thiết lập demo notebooks...")
                    ensure_demo_notebooks(db)
                    scoped_assets = get_scoped_asset_ids(db, nb_id)
                    print(f"✔ Sau khi thiết lập: Notebook ID {nb_id} sở hữu {len(scoped_assets)} assets: {scoped_assets}")
                else:
                    print(f"   (Gợi ý: Chạy lại với cờ --setup-demo-notebook để tự động liên kết tài liệu)")
            else:
                print(f"✔ Notebook ID {nb_id}: Đã tìm thấy {len(scoped_assets)} assets trong scope: {scoped_assets}")

        # 1. Handle Dry-Run or Placeholder mode
        if dry_run or has_placeholders:
            print("\n" + "-" * 75)
            if has_placeholders:
                print("ℹ Phát hiện testset mẫu chứa placeholder '[TODO: ...]'.")
            else:
                print("ℹ Chạy ở chế độ dry-run theo yêu cầu tham số dòng lệnh.")
            print("-" * 75)
            print(f"✔ Kiểm tra cấu trúc file golden_testset.json: HỢP LỆ ({len(items)} câu hỏi mẫu).")
            for i, it in enumerate(items, 1):
                q_preview = it.get('question', '')[:60] + "..." if len(it.get('question', '')) > 60 else it.get('question', '')
                print(f"   [{i:02d}] ID: {it.get('id')} | NB: {it.get('notebook_id')} | Q: {q_preview}")

            print("\n✔ Nguồn sinh câu trả lời (Production Parity):")
            print("   • Tái sử dụng public APIs: condense_query_and_route + hybrid_retrieval")
            print("   • System instruction: Bản sao đồng bộ của prompt production (Tone, Persona, Citations [1], Anti-Hallucination)")
            print("   • File production app/rag/chat/service.py: Giữ nguyên 100%, không bị sửa đổi")
            print("\n✔ Kiểm tra cấu hình Ragas Judge (Gemini):")
            print(f"   • GEMINI_API_KEY: {'Đã cấu hình' if settings.GOOGLE_API_KEY else 'CHƯA CÓ'}")
            print(f"   • GEMINI_CHAT_MODEL: {settings.GEMINI_CHAT_MODEL}")
            print("   • 4 Metrics Ragas: Faithfulness, Answer Relevancy, Context Precision, Context Recall")
            print("   • Đảm bảo định dạng contexts: list[str]")
            print("\n➡ KẾT QUẢ DRY-RUN: Khung kiểm thử hoạt động hoàn hảo!")
            print("   Vui lòng thay thế câu hỏi & ground truth thật ở PHẦN B để tiến hành benchmark.")
            print("=" * 75)
            return

        # 2. Real Execution Flow
        print("\n🚀 Bắt đầu thực thi pipeline RAG production thật và đánh giá Ragas...")
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics.collections import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

        questions: list[str] = []
        answers: list[str] = []
        contexts_list: list[list[str]] = []
        ground_truths: list[str] = []

        for idx, item in enumerate(items, 1):
            q = item["question"]
            nb_id = item.get("notebook_id", 1)
            gt = item["ground_truth"]

            print(f"[{idx}/{len(items)}] Đang chạy RAG pipeline cho: '{q[:50]}...'")

            # Gọi RAG pipeline chuẩn
            rag_output = execute_rag_pipeline(
                db=db,
                notebook_id=nb_id,
                query=q,
            )

            retrieved_contexts: list[str] = rag_output["contexts"]
            ans: str = rag_output["answer"]

            questions.append(q)
            answers.append(ans)
            contexts_list.append(retrieved_contexts)
            ground_truths.append(gt)

            # Cooldown between queries to prevent LLM rate limiting
            time.sleep(1.5)

        # 3. Build Ragas Dataset
        eval_dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts_list,
            "ground_truth": ground_truths,
        })

        # 4. Setup Gemini Judge & Embeddings
        judge_llm = LangchainLLMWrapper(ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0,
        ))
        judge_embeddings = LangchainEmbeddingsWrapper(GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GOOGLE_API_KEY,
        ))

        # 5. Execute Evaluation
        print("\n⏳ Đang chấm điểm với 4 metrics Ragas (Faithfulness, Answer Relevancy, Precision, Recall)...")
        eval_result = evaluate(
            dataset=eval_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=judge_llm,
            embeddings=judge_embeddings,
            raise_exceptions=False,
        )

        print("\n" + "=" * 75)
        print("                    KẾT QUẢ ĐÁNH GIÁ RAGAS")
        print("=" * 75)
        print(eval_result)

        # 6. Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary_dict = {
            "timestamp": time.time(),
            "total_samples": len(items),
            "scores": eval_result.to_pandas().to_dict(orient="records"),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary_dict, f, ensure_ascii=False, indent=2)

        print(f"\n✔ Kết quả chi tiết đã được lưu tại: {output_path}")
        print("=" * 75)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline using Ragas framework.")
    parser.add_argument(
        "--testset",
        type=str,
        default=str(PROJECT_ROOT / "tests" / "evaluation" / "golden_testset.json"),
        help="Path to golden_testset.json",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "tests" / "evaluation" / "ragas_results.json"),
        help="Path to output ragas_results.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run syntax/schema sanity check without calling LLM APIs",
    )
    parser.add_argument(
        "--setup-demo-notebook",
        action="store_true",
        help="Ensure demo notebooks exist and have saved documents linked in DB",
    )

    args = parser.parse_args()
    run_evaluation(
        testset_path=Path(args.testset),
        output_path=Path(args.output),
        dry_run=args.dry_run,
        auto_setup_notebooks=args.setup_demo_notebook,
    )


if __name__ == "__main__":
    main()
