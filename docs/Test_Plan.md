# Kế hoạch & Báo cáo Kiểm thử (Test Plan & Test Report)

## Knowledge Sharing Platform — Backend & System Verification

---

## 1. Mục tiêu & Phạm vi Kiểm thử (Testing Objectives & Scope)

### 1.1. Mục tiêu
- Đảm bảo độ tin cậy và tính đúng đắn của toàn bộ các dịch vụ nghiệp vụ cốt lõi trong hệ thống: Authentication, Ingestion Pipeline, Two-Stage Retrieval Engine, SSE Streaming Chat, Quiz Studio Artifacts và Cổng thanh toán VNPay.
- Xác thực các ràng buộc an toàn: Chống Race Condition trong thanh toán (Pessimistic Lock), Chống vượt hạn mức gói cước (Soft-cap Quota Enforcement), và Cơ chế tái sử dụng vector embedding (SHA-256 Deduplication).

### 1.2. Môi trường & Công cụ kiểm thử
- **Framework kiểm thử:** `pytest` (v9.1.1), `pytest-asyncio` (v0.25+), `anyio`.
- **Client mô phỏng HTTP:** `fastapi.testclient.TestClient` (HTTPX-based).
- **Môi trường:** Python 3.12, Virtualenv `backend/.venv`, PostgreSQL 16 + pgvector.

---

## 2. Bảng Tổng hợp 12 Bộ Kiểm thử Tự động (12 Test Suites Summary)

Toàn bộ 12 test suites được thiết kế độc lập, có cơ chế mock các dịch vụ bên ngoài (Google Gemini API, Jina AI, VNPay Gateway) để kiểm tra chính xác logic nội bộ của ứng dụng mà không phát sinh chi phí token API:

| Mã Suite | File Kiểm thử | Phân hệ / Tính năng kiểm tra | Số ca test | Trạng thái |
| :---: | :--- | :--- | :---: | :---: |
| **TS-01** | `tests/test_payments.py` | Tạo đơn hàng VNPay, Ký số HMAC-SHA512, Xử lý IPN Webhook, Idempotency Guard, Cộng dồn 30 ngày Pro | 6 | ✅ PASS |
| **TS-02** | `tests/test_conversion.py` | Chuyển đổi DOCX → PDF bằng LibreOffice headless, Quản lý tiến trình subprocess, Dọn file rác tạm | 3 | ✅ PASS |
| **TS-03** | `tests/test_ingestion_pipeline.py` | Bóc tách text từng trang qua generator, Sentence-Aware Chunking, Ghi chỉ mục Vector pgvector | 3 | ✅ PASS |
| **TS-04** | `tests/test_ingestion_dedup.py` | Tính toán mã băm SHA-256 (`file_hash`), Tái sử dụng `AssetEmbedding` có sẵn khi trùng tệp | 2 | ✅ PASS |
| **TS-05** | `tests/test_embeddings.py` | Embedding Provider (Gemini / Jina), Sliding-Window Rate Limiter, Cơ chế Dynamic Batching | 3 | ✅ PASS |
| **TS-06** | `tests/test_hybrid_search.py` | Tầng 1: Dense Search (HNSW) + Sparse Search (GIN), Công thức RRF ($k=60$), Gộp chunk liền kề | 4 | ✅ PASS |
| **TS-07** | `tests/test_reranker.py` | Tầng 2: Jina Cross-Encoder Reranking, Lọc Top-15 thành Top-5, Fallback về NoOpProvider khi lỗi mạng | 3 | ✅ PASS |
| **TS-08** | `tests/test_condensation.py` | Rút gọn câu truy vấn, Phân loại ý định `needs_rag`, Fast-path bypass cho tin nhắn đầu | 3 | ✅ PASS |
| **TS-09** | `tests/test_chat_sse.py` | Giao thức SSE Streaming: Bắn sự kiện `citations`, `delta`, `done`, Lưu hội thoại vào DB | 3 | ✅ PASS |
| **TS-10** | `tests/test_notebook_chat.py` | Quản lý phiên chat (Session), Phân quyền sở hữu sổ tay, Ràng buộc dữ liệu tin nhắn | 3 | ✅ PASS |
| **TS-11** | `tests/test_quiz_generation.py` | Thuật toán Multi-Asset Linspace Sampling, Sinh câu hỏi trắc nghiệm qua Gemini Structured Output | 3 | ✅ PASS |
| **TS-12** | `tests/test_notebook_artifact.py` | CRUD Artifacts, Kiểm soát Cooldown 10s chống spam, Kiểm soát hạn mức Soft-cap Free/Pro | 3 | ✅ PASS |
| **TỔNG** | **12 Test Suites** | **Toàn bộ dịch vụ cốt lõi Backend** | **39 Tests** | **100% PASS** |

---

## 3. Ma trận Kịch bản Kiểm thử Điển hình (Detailed Test Cases Matrix)

| Test ID | Kịch bản kiểm thử (Test Scenario) | Dữ liệu đầu vào (Input) | Kết quả kỳ vọng (Expected Output) | Kết quả thực tế |
| :--- | :--- | :--- | :--- | :---: |
| **TC-PAY-01** | Tạo link thanh toán VNPay | User hợp lệ, Gói Pro 50.000 VNĐ | Trả về `payment_url` hợp lệ chứa đúng `vnp_SecureHash` chuẩn SHA-512 | ✅ Đạt |
| **TC-PAY-02** | Xử lý thanh toán đồng thời (Race Condition) | 2 request IPN cùng đơn hàng gửi đồng thời | Nhờ `SELECT FOR UPDATE`, chỉ 1 request xử lý thành công; request sau nhận mã 02 (Đã xử lý) | ✅ Đạt |
| **TC-PAY-03** | Gia hạn Pro cộng dồn | User còn hạn Pro 10 ngày | Hạn mới = Ngày hết hạn hiện tại + 30 ngày (Tổng 40 ngày) | ✅ Đạt |
| **TC-ING-01** | Deduplication chống trùng lặp file | Upload file có SHA-256 đã tồn tại | Hệ thống tái sử dụng embeddings cũ, số lần gọi API embedding = 0 | ✅ Đạt |
| **TC-ING-02** | Chunking bảo toàn ranh giới trang | Tài liệu văn bản dài qua nhiều trang | Tuyệt đối không chunk nào bị cắt vắt ngang 2 trang khác nhau | ✅ Đạt |
| **TC-RAG-01** | Hợp nhất Hybrid Search RRF | Câu hỏi tra cứu học phần | Candidate pool Top-15 được xếp hạng chính xác theo công thức $RRF = \sum \frac{1}{60 + \text{rank}}$ | ✅ Đạt |
| **TC-RAG-02** | Cross-Encoder Reranking | Pool Top-15 chunk | Lọc chính xác đúng Top-5 chunk có điểm ngữ nghĩa cao nhất | ✅ Đạt |
| **TC-RAG-03** | Adjacent Chunk Stitching | 2 chunk liền kề cùng trang | Gộp 2 chunk thành 1 đoạn duy nhất, đánh số trích dẫn đồng bộ | ✅ Đạt |
| **TC-SSE-01** | Truyền dữ liệu SSE Stream | Gửi tin nhắn vào phiên chat | Bắn sự kiện `citations` trước, theo sau là chuỗi `delta` và kết thúc bằng `done` | ✅ Đạt |
| **TC-QUIZ-01**| Sinh câu hỏi trắc nghiệm | 2 tài liệu trong sổ tay, yêu cầu 5 câu | Linspace sampling lấy mẫu đều 2 tài liệu; JSON sinh ra có đúng 5 câu hỏi và 4 lựa chọn | ✅ Đạt |
| **TC-QUOTA-01**| Chặn tạo bài tập khi hết hạn mức Free | User Free đã có 10 bài tập | Ném ngoại lệ HTTP 403 Forbidden: "Đã đạt giới hạn tối đa 10 bài tập" | ✅ Đạt |
| **TC-QUOTA-02**| Cooldown chống spam | Gọi sinh bài tập 2 lần liên tiếp < 10s | Ném ngoại lệ HTTP 429 Too Many Requests kèm số giây còn lại | ✅ Đạt |

---

## 4. Hướng dẫn Chạy Kiểm thử (Test Execution Guide)

Để chạy toàn bộ bộ kiểm thử tự động trên máy local:

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Kích hoạt môi trường ảo Python
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Chạy toàn bộ 12 test suites với pytest
pytest -v

# 4. (Tùy chọn) Chạy riêng một phân hệ cụ thể (ví dụ Payment):
pytest tests/test_payments.py -v
```
