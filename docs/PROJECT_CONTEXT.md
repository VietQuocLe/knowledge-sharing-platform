# PROJECT_CONTEXT.md

# Knowledge Sharing Platform

> Graduation Project — AI-powered Knowledge Sharing Platform inspired by Studocu + NotebookLM

---

# 1. Project Overview

## Description
Knowledge Sharing Platform là hệ thống chia sẻ học liệu kết hợp trợ lý AI học tập. Hệ thống tổ chức học liệu công khai theo cấu trúc phân cấp: **Khoa (Department) → Ngành (Major) → Môn học (Subject) → Tài liệu (Document)**. Đồng thời, nền tảng cung cấp không gian học tập cá nhân hóa (**AI Notebook Workspace**), cho phép người học lưu trữ tài liệu từ thư viện công cộng hoặc tải lên tài liệu cá nhân để tra cứu, hỏi đáp thông minh qua RAG (Retrieval-Augmented Generation), sinh bài tập trắc nghiệm ôn tập (Quiz Studio), và nâng cấp tài khoản Pro qua cổng thanh toán VNPay.

---

# 2. Project Roadmap & Sprint History

| Giai đoạn / Sprint | Phân hệ / Tính năng | Trạng thái | Tóm tắt nội dung kỹ thuật thực hiện |
| :--- | :--- | :---: | :--- |
| **Sprint 1–5** | **Backend Core & Upload** | ✅ Hoàn thành | Khung FastAPI, Auth (Argon2id, JWT), CRUD Taxonomy (Khoa/Ngành/Môn học), upload PDF/DOCX lưu MinIO. |
| **Sprint 6–8** | **Frontend Foundation** | ✅ Hoàn thành | React 19 + TypeScript + Vite + Tailwind CSS, TanStack Query v5, AppLayout, PublicLayout, AuthContext. |
| **Sprint 8.5** | **DB Architecture Refactor** | ✅ Hoàn thành | Tách `Resource` cũ thành `Document` (Public) và `Notebook` (Private Workspace); bảng liên kết `Asset` và `NotebookSavedDocument`. |
| **Sprint 9** | **UI/UX & Design Polish** | ✅ Hoàn thành | Luồng khám phá Progressive Disclosure, debounced search môn học, UI components chuẩn hóa (`Badge`, `Card`, `Modal`). |
| **Sprint 10–10.5** | **Notebook Management** | ✅ Hoàn thành | Dashboard Sổ tay cá nhân (`/me/workspace`), CRUD Notebook (đổi tên, xóa mềm, dọn MinIO nền). |
| **Sprint 11** | **Notebook Detail & Source Linking** | ✅ Hoàn thành | Split-view layout, lưu tài liệu Public vào Sổ tay, upload tệp cá nhân (magic-bytes guard, giới hạn 30MB). |
| **Sprint 11.5** | **Document Conversion Engine** | ✅ Hoàn thành | Chuyển đổi DOCX → PDF phái sinh bằng LibreOffice headless (`soffice`), mở khóa xem trước DOCX trên giao diện. |
| **Sprint 12** | **Ingestion Pipeline Core** | ✅ Hoàn thành | Trích xuất text theo trang `pypdfium2`, page-aware chunking, batch embedding qua `gemini-embedding-001` (768d), lưu bảng `AssetEmbedding` (pgvector HNSW). |
| **Sprint 13–14** | **Retrieval Engine & Chat UI** | ✅ Hoàn thành | Hybrid Search RRF (Dense HNSW + Sparse GIN), query condensation sliding-window, SSE streaming chat, Citation UI click nhảy trang PDF (`#page=X`). |
| **Sprint 15–16** | **Quiz Studio (AI Artifacts)** | ✅ Hoàn thành | Thuật toán Multi-Asset Linspace Sampling, Bloom reasoning prompt, Google GenAI Structured JSON Output, trình làm bài `QuizRunner` tương tác. |
| **Sprint 16.5** | **Service Hardening & Optimization** | ✅ Hoàn thành | Content-addressable Deduplication (SHA-256), Streaming PDF memory (<30MB RAM), Dual-mode conversion (Cloudmersive REST API fallback LibreOffice), Google OAuth 2.0, Soft Pastel theme, Langfuse Cloud tracing. |
| **Sprint 16.6** | **Centralized Settings & Observability** | ✅ Hoàn thành | 22+ Pydantic Settings fields trong `config.py` (loại bỏ toàn bộ magic numbers trong service layer), Langfuse v4 SDK compatibility, CLI script `seed_data.py`. |
| **RAG Upgrade (Post-16.6)** | **Two-Stage Retrieval & Jina AI** | ✅ Hoàn thành | Tái cấu trúc package `backend/app/rag/`, tích hợp Strategy Pattern `EmbeddingProvider` (bổ sung `jina-embeddings-v3` MRL 768d), bổ sung Cross-Encoder `jina-reranker-v2-base-multilingual` (Top-15 → Top-5), nâng cấp chunking `SentenceSplitter` (`llama-index-core` + `underthesea`), Rate Limiter sliding-window (`_EMBEDDING_SEMAPHORE` + `EmbeddingRateLimiter`). |
| **Payment (Post-16.6)** | **Payment & Subscription (VNPay)** | ✅ Hoàn thành | Tích hợp cổng VNPay Sandbox 2.1.0 (HMAC-SHA512), model `PaymentOrder`, Pessimistic Lock Idempotency Guard (`SELECT ... FOR UPDATE`), cơ chế cộng dồn 30 ngày Pro, Lazy Downgrade tier (`quota_service.py`), giao diện `PricingModal` & `PaymentReturnPage`. |
| **Sprint 17** | **Testing & Evaluation** | 🔄 Đang triển khai | Backend: 12 test suites phủ toàn bộ services; Framework Ragas (`eval_ragas.py`). Frontend: chưa có test tự động. |
| **Sprint 18** | **Deployment & Optimization** | ⏳ Kế hoạch | Dockerize production, chuyển Cloud (Render/Vercel/Supabase/R2) qua `.env`, tối ưu chi phí token. |

---

# 3. System Architecture & Modules Status

### 3.1. Authentication, Phân quyền & Quản lý Gói cước
* **Cơ chế xác thực:** Đăng ký, đăng nhập bằng Email/Password (mã hóa Argon2id qua `pwdlib`), cấp Access Token JWT (HS256, thời hạn 24 giờ).
* **Google OAuth 2.0:** Endpoint `POST /auth/google` tiếp nhận Google ID token từ frontend (`@react-oauth/google`), tự động liên kết hoặc tạo tài khoản mới.
* **Phân quyền hệ thống (RBAC):** Kiểm soát qua enum `UserRole` với 2 quyền thực tế:
  * `USER`: Người học thông thường, truy cập thư viện, sử dụng Notebook và tính năng AI trong hạn mức.
  * `ADMIN`: Quản trị viên hệ thống (tự động khởi tạo từ `settings.ADMIN_EMAIL`), có toàn quyền CRUD danh mục Khoa, Ngành, Môn học.
  *(Ghi chú: Giá trị enum `PREMIUM_USER` tồn tại trong schema ban đầu nhưng không dùng để phân quyền; toàn bộ quyền lợi nâng cao được điều khiển độc lập qua trường `tier`).*
* **Quản lý gói cước (Subscription Tier):** Model `User` lưu trữ trường `tier` (`SubscriptionTier.FREE` hoặc `PRO`) và `pro_expires_at` (thời điểm hết hạn Pro).

### 3.2. Taxonomy & Public Document Library
* **Phân cấp đào tạo:** Khoa (`Department`) → Ngành (`Major`) → Môn học (`Subject`). Hỗ trợ tìm kiếm môn học tức thì không phân biệt dấu tiếng Việt.
* **Tài liệu học tập (`Document`):** Gắn liền với Môn học (`subject_id`), phân loại theo `ResourceType` (`SLIDE`, `EXAM`, `DOCUMENT`, `LECTURE`...).
* **Trạng thái xuất bản:** `DocumentStatus` (`DRAFT`, `PUBLIC`, `DELETED`). Tài liệu trong thư viện hiện tại được seed trực tiếp ở trạng thái `PUBLIC`.
* **Tải tệp tin:** Cấp presigned URL trực tiếp từ MinIO (thời hạn 15 phút) thông qua endpoint `GET /documents/{id}/assets/{asset_id}/download`, không yêu cầu JWT để tối ưu tốc độ tải.

### 3.3. AI Workspace (Notebook cá nhân & Hạn mức)
* **Không gian làm việc (`Notebook`):** Thuộc sở hữu của từng người dùng (`owner_id`), hỗ trợ đổi tên và xóa mềm (kèm dọn dẹp file vật lý MinIO chạy nền).
* **Nguồn tài liệu kép (Dual-Source):** Một Notebook chứa tối đa các nguồn từ 2 dạng:
  1. Tài liệu thư viện liên kết logic (`NotebookSavedDocument` trỏ sang `Document`, không nhân bản file vật lý).
  2. Tệp cá nhân người dùng tự tải lên (`Asset` thuộc `Notebook`, giới hạn 30MB, kiểm định magic bytes PDF/DOCX).
* **Chính sách hạn mức theo Gói cước (Tier-based Soft-cap):**
  * **Tài khoản FREE:** Tối đa **8 nguồn tài liệu** (`FREE_MAX_SOURCES = 8`) và **10 bài tập trắc nghiệm** (`FREE_MAX_ARTIFACTS = 10`).
  * **Tài khoản PRO:** Tối đa **20 nguồn tài liệu** (`PRO_MAX_SOURCES = 20`) và **20 bài tập trắc nghiệm** (`PRO_MAX_ARTIFACTS = 20`).
  * Cơ chế chặn mềm (Soft-cap Policy): Không bao giờ xóa hay ẩn tài liệu cũ của người dùng; chỉ chặn khi thêm nguồn mới nếu số lượng hiện tại đã đạt hoặc vượt ngưỡng.

### 3.4. Document Processing & Ingestion Pipeline
* **Dual-Mode Document Conversion:** Khi tải lên file `.docx`, hệ thống ưu tiên gọi **Cloudmersive REST API** để chuyển đổi sang PDF phái sinh (giải phóng RAM/CPU của server); tự động fallback sang subprocess **LibreOffice headless** (`soffice`) khi chạy local/offline.
* **Streaming Text Extraction:** Dùng `pypdfium2` duyệt từng trang độc lập dưới dạng generator. Tài nguyên C-layer (`page.close()`, `textpage.close()`) được giải phóng ngay sau mỗi trang, duy trì bộ nhớ RAM luôn dưới $30\text{MB}$.
* **Sentence-Aware Chunking:** Sử dụng `SentenceSplitter` từ `llama-index-core` kết hợp thư viện tách câu tiếng Việt `underthesea` (`safe_sent_tokenize`). Chia đoạn theo ranh giới câu (500–700 tokens, overlap 100 tokens), **tuyệt đối không cắt chunk vắt ngang qua ranh giới trang** để đảm bảo trích dẫn citation chuẩn xác 100%.
* **Content-addressable Deduplication:** Kiểm tra mã băm SHA-256 (`file_hash`). Nếu file đã từng được ingest thành công, hệ thống tái sử dụng toàn bộ bản ghi `AssetEmbedding` có sẵn sang `asset_id` mới mà không gọi API embedding, tiết kiệm 100% thời gian và chi phí AI.
* **Embedding Providers (Strategy Pattern):** Hỗ trợ chuyển đổi linh hoạt qua biến môi trường `EMBEDDING_PROVIDER`:
  * `GeminiEmbeddingProvider`: Dùng `gemini-embedding-001`, cấu hình MRL `output_dimensionality=768`.
  * `JinaEmbeddingProvider`: Dùng `jina-embeddings-v3`, MRL `dimensions=768`, task `retrieval.passage` cho tài liệu và `retrieval.query` cho câu hỏi.
  * Factory `get_embedding_provider()` tự động fallback về Gemini nếu thiếu `JINA_API_KEY`.
* **Rate Limiting & Dynamic Batching:**
  * `_EMBEDDING_SEMAPHORE`: `threading.Semaphore(1)` đơn luồng hóa toàn bộ lời gọi embedding.
  * `EmbeddingRateLimiter`: Cơ chế Sliding-Window kiểm soát đồng bộ cả RPM và TPM, tự động sleep điều tiết.
  * Gom batch động dựa trên cấu hình `ACTIVE_EMBEDDING_*` (Gemini: budget 24k tokens, max 80 chunks; Jina: budget 25k tokens, max 50 chunks).

### 3.5. Two-Stage Retrieval Engine
* **Tầng 1 (Hybrid Search RRF):**
  * **Dense Search:** Vector Cosine Distance trên chỉ mục HNSW (`vector_cosine_ops`, tham số `m=16`, `ef_construction=64`) của cột `embedding VECTOR(768)`. Lấy Top-20 (`RAG_DENSE_SEARCH_TOP_K = 20`).
  * **Sparse Search:** Full-text Search trên chỉ mục GIN của cột `tsv_content` (Generated Column `to_tsvector('simple', immutable_unaccent(content))`), xếp hạng bằng `ts_rank_cd`. Lấy Top-20 (`RAG_SPARSE_SEARCH_TOP_K = 20`).
  * **Hợp nhất RRF:** Tính điểm theo công thức Reciprocal Rank Fusion ($k=60.0$):
    $$RRF(d) = \sum_{r \in \text{Dense, Sparse}} \frac{1}{60 + \text{rank}_r(d)}$$
  * Trích xuất **Candidate Pool Top-15** (`RAG_RRF_POOL_SIZE = 15`).
* **Tầng 2 (Cross-Encoder Reranking):**
  * Mô hình `jina-reranker-v2-base-multilingual` chấm lại điểm mức độ liên quan ngữ nghĩa trực tiếp giữa câu hỏi và từng chunk trong Pool Top-15, chắt lọc lại đúng **Top-5 kết quả tốt nhất** (`RAG_RERANK_TOP_N = 5`).
  * Nếu tắt Reranker hoặc gặp sự cố kết nối, hệ thống tự động fallback về `NoOpProvider` giữ nguyên thứ tự RRF.
* **Tầng 3 (Post-processing):**
  * **Adjacent Chunk Stitching:** Tự động gộp các chunk liền kề (cùng `asset_id`, cùng `page_number`, `chunk_index` liên tiếp) thành một khối thống nhất để bảo toàn ngữ cảnh liền mạch cho LLM.
  * **Token Budget Enforcement:** Cắt tỉa ngữ cảnh không vượt quá 3000 tokens (`RAG_CONTEXT_MAX_TOKENS = 3000`).
  * **Citation Renumbering:** Đánh số lại trích dẫn `[1]..[N]` đồng bộ cho cả prompt context và metadata gửi về client.

### 3.6. RAG Chat & SSE Streaming
* **Intent Routing & Query Condensation:** Mô hình `gemini-3.1-flash-lite` phân tích 6 lượt hội thoại gần nhất (`CHAT_HISTORY_SLIDING_WINDOW_SIZE = 6`) để rút gọn câu hỏi và phân loại ý định `needs_rag`. Lượt chat đầu tiên có cơ chế fast-path bypass để giảm độ trễ.
* **Giao thức SSE Stream:** Endpoint `POST /notebooks/{id}/sessions/{session_id}/chat` truyền dữ liệu theo 4 sự kiện chuẩn:
  1. `event: citations`: Bắn danh sách trích dẫn nguồn ngay khi hoàn thành retrieval (trước khi LLM sinh từ).
  2. `event: delta`: Truyền từng đoạn token văn bản thô theo thời gian thực.
  3. `event: done`: Gửi mã định danh tin nhắn đã lưu, số lượng token thực tế và câu truy vấn rút gọn.
  4. `event: error`: Thông báo lỗi nếu luồng sinh bị gián đoạn.
* **Concurrency & Safety:** Sử dụng `asyncio.Lock` theo từng `session_id` ngăn chặn gửi 2 câu hỏi song song (lỗi 409 Conflict); ghi dữ liệu nguyên tử (atomic write-on-complete) chỉ lưu tin nhắn khi hoàn tất stream.

### 3.7. Quiz Studio (AI Artifacts)
* **Sampling đa tài liệu (Multi-Asset Linspace):** Thuật toán phân bổ ngân sách 30 chunks đều cho các tài liệu được chọn, lấy mẫu khoảng cách đều:
  $$\text{index}_i = \text{round}\left( \frac{i \times (\text{total\_chunks} - 1)}{\text{budget\_per\_asset} - 1} \right)$$
  Bảo đảm bao phủ 100% tài liệu từ chunk mở đầu (`index = 0`) đến chunk kết luận cuối cùng (`index = N - 1`), triệt tiêu hiện tượng bỏ sót nội dung cuối file.
* **Structured Output & Bloom Taxonomy:** Gọi `gemini-3.1-flash-lite` với `response_schema=QuizContentPayload`. Tỷ lệ câu hỏi: 30% Nhận biết / Thông hiểu, 70% Vận dụng / Suy luận. Cấu trúc lời giải thích 3 tầng (Bản chất lý thuyết → Suy luận logic → Giải thích vì sao các phương án khác sai).
* **Frontend Quiz Runner:** Trình làm bài tương tác, chấm điểm trực tiếp, giải thích chi tiết, lưu trữ kết quả và đồng bộ trạng thái URL qua `?artifact={id}`.

### 3.8. Payment & Subscription System (VNPay)
* **Cổng thanh toán:** Tích hợp VNPay Sandbox chuẩn 2.1.0 với thuật toán ký số bảo mật `HMAC-SHA512`.
* **Gói cước Pro:** Giá niêm yết 49.000 VNĐ/tháng (`PRO_PLAN_PRICE = 49000`), thanh toán mở rộng hạn mức lên 20 nguồn tài liệu và 20 bài quiz.
* **Idempotency Guard:** Sử dụng Pessimistic Locking (`SELECT ... FOR UPDATE`) trong transaction cơ sở dữ liệu để chống race condition khi cả Return URL (từ trình duyệt người dùng) và Webhook IPN (từ server VNPay) kích hoạt đồng thời.
* **Cộng dồn thời hạn:** Nếu tài khoản Pro vẫn còn hạn, thời gian 30 ngày mới sẽ được cộng nối tiếp từ mốc `pro_expires_at` hiện tại.
* **Lazy Downgrade ([`quota_service.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/app/services/quota_service.py)):** Kiểm tra thời hạn Pro ngay khi người dùng thực hiện request nghiệp vụ; tự động chuyển về `FREE` nếu đã quá hạn mà không cần setup cron job hay worker Celery phức tạp.

### 3.9. Quản trị hệ thống (Admin)
* **Taxonomy Management:** Giao diện `/admin/taxonomy` hoạt động đầy đủ, cho phép Admin tạo mới, chỉnh sửa và xóa Khoa, Ngành, Môn học (hỗ trợ redirect tạm thời từ `/admin` sang `/admin/taxonomy`).
* **Document Moderation:** Đã loại bỏ hoàn toàn khỏi phạm vi triển khai và đưa vào Backlog định hướng mở rộng sau tốt nghiệp. Tài liệu cộng đồng hiện được tiếp nhận chuẩn hóa qua Google Forms và đưa vào hệ thống qua seed script (`seed_data.py`).
* **Định hướng mở rộng tiếp theo (chưa triển khai):** CRUD Users + quản lý tier/quota thủ công (xem danh sách user, điều chỉnh tier PRO/FREE, chỉnh ngày hết hạn `pro_expires_at`, xem usage nguồn/quiz cơ bản qua `quota_service.py`) — giải pháp rủi ro thấp do không chạm vào core RAG pipeline; ưu tiên thấp hơn viết report, sẽ thực hiện nếu còn thời gian trước khi nộp/bảo vệ.

---

# 4. Quyết định Kỹ thuật & Lý do Lựa chọn (Architectural Decisions & Rationale)

> Phần này tổng hợp các quyết định kỹ thuật cốt lõi (Justification) phục vụ cho thuyết minh kiến trúc và báo cáo đồ án tốt nghiệp:

1. **Hybrid Search RRF thay vì chỉ Vector Search thuần túy:**
   * *Vấn đề:* Tiếng Việt học thuật chứa rất nhiều thuật ngữ chuyên ngành, mã môn học (ví dụ: CS101, KTLT), tên riêng và từ viết tắt mà các mô hình vector embedding thuần rất dễ bỏ sót hoặc trả về độ tương đồng giả.
   * *Giải pháp:* Kết hợp Dense Retrieval (HNSW cosine) bắt ngữ nghĩa câu hỏi tự do với Sparse Retrieval (GIN full-text search) bắt chính xác từ khóa. Sử dụng **Reciprocal Rank Fusion (RRF)** hợp nhất theo thứ hạng (rank) thay vì điểm số (score), giải quyết triệt để vấn đề thang đo điểm số không tương đồng giữa hai phương pháp mà không cần tinh chỉnh trọng số thủ công.
2. **Kiến trúc Hand-Rolled Core kết hợp Thư viện Chuyên biệt (Tránh Framework cồng kềnh):**
   * *Vấn đề:* Các framework RAG toàn diện (như LangChain, LlamaIndex end-to-end) tạo ra các lớp abstraction quá dày, khó kiểm soát prompt, khó tối ưu hóa độ trễ streaming SSE và khó kiểm soát chi phí token.
   * *Giải pháp:* Tự xây dựng (hand-rolled) toàn bộ luồng Storage, SQL Retrieval, RRF Fusion, SSE Chat Engine và Linspace Sampling. Chỉ mượn duy nhất một component chuyên biệt là `SentenceSplitter` của `llama-index-core` kết hợp thư viện NLP tiếng Việt `underthesea` cho khâu cắt câu ở tầng Ingestion Chunking.
3. **Cắt vector 768 chiều (Matryoshka Representation Learning - MRL):**
   * *Lý do:* Cả `gemini-embedding-001` và `jina-embeddings-v3` đều được huấn luyện hỗ trợ MRL. Việc cắt lát vector về 768 chiều (thay vì 1024 hay 3072) vừa khớp hoàn hảo kiểu cột `VECTOR(768)` trong PostgreSQL, vừa giảm 25%–75% dung lượng chỉ mục HNSW và chi phí lưu trữ/tính toán trong RAM mà chất lượng truy hồi gần như không đổi.
4. **Xử lý tiếng Việt không dấu ở tầng Cơ sở dữ liệu (`unaccent` + Generated Column):**
   * *Lý do:* Bổ sung extension `unaccent` và wrapper `immutable_unaccent()` để tạo cột `tsv_content` dưới dạng Generated Column (`GENERATED ALWAYS AS`). Cơ chế này đảm bảo người dùng gõ có dấu hay không dấu đều khớp, và tsvector luôn tự động đồng bộ từ nội dung chunk mà không cần viết code Python xử lý mỗi lần ghi.
5. **Chuẩn hóa DOCX → PDF phái sinh thay vì parse DOCX riêng biệt:**
   * *Lý do:* Chuyển đổi DOCX sang bản PDF phái sinh giúp toàn bộ pipeline AI chỉ xử lý **một định dạng đầu vào duy nhất** qua `pypdfium2`. Đồng thời, số trang trích dẫn trong citation (`#page=X`) luôn khớp chính xác 100% với bản PDF mà người học đang xem trực tiếp trên giao diện.
6. **Page-aware Chunking (Không gối đầu xuyên trang):**
   * *Lý do:* Giới hạn việc cắt chunk trong phạm vi từng trang tài liệu, tuyệt đối không tạo overlap xuyên qua ranh giới trang. Đánh đổi một phần nhỏ ngữ cảnh ở biên trang để tính năng click-to-jump citation trên giao diện mở đúng trang nguồn mà không bị lệch trang.
7. **Thiết kế Local-First & Cloud-Ready:**
   * *Lý do:* Toàn bộ hệ thống chạy hoàn chỉnh ở môi trường local qua Docker Compose (PostgreSQL 16, pgvector, MinIO, LibreOffice). Khi triển khai production, toàn bộ hạ tầng có thể chuyển sang dịch vụ Cloud (Render cho Backend, Vercel cho Frontend, Supabase cho Postgres, Cloudflare R2 cho MinIO, Cloudmersive cho Office conversion) chỉ bằng cách đổi biến môi trường trong `.env`, không phải sửa mã nguồn.

---

# 5. Detailed Technical Specifications

### 5.1. Ingestion, Chunking & Embedding Parameters

| Cấu hình | Biến trong `config.py` | Giá trị mặc định | Ý nghĩa |
| :--- | :--- | :--- | :--- |
| Chunk Size | `INGESTION_CHUNK_SIZE_WORDS` | `600` | Số từ mục tiêu cho mỗi chunk |
| Chunk Overlap | `INGESTION_CHUNK_OVERLAP_WORDS` | `100` | Số từ gối đầu giữa 2 chunk trong cùng 1 trang |
| Scanned Threshold | `INGESTION_MIN_PDF_CHAR_THRESHOLD` | `100` | Ký tự tối thiểu mỗi trang để nhận diện không phải PDF scan |
| Active Provider | `EMBEDDING_PROVIDER` | `"gemini"` | Nhà cung cấp embedding (`"gemini"` hoặc `"jina"`) |
| Vector Dimension | `EMBEDDING_DIMENSION` | `768` | Số chiều vector embedding (MRL) khớp cột `VECTOR(768)` |
| Gemini RPM Limit | `GEMINI_EMBEDDING_RPM_LIMIT` | `80` | Giới hạn Request/phút của Gemini free tier |
| Gemini TPM Limit | `GEMINI_EMBEDDING_TPM_LIMIT` | `26000` | Giới hạn Tokens/phút của Gemini free tier |
| Gemini Batch Chunks | `GEMINI_EMBEDDING_MAX_CHUNKS_PER_BATCH` | `80` | Số chunk tối đa gửi sang Gemini trong một batch |
| Gemini Batch TPM Budget | `GEMINI_EMBEDDING_TPM_BUDGET_PER_BATCH` | `24000` | Ngân sách token an toàn cho một batch Gemini |
| Jina Model | `JINA_EMBEDDING_MODEL` | `"jina-embeddings-v3"` | Model embedding đa ngữ của Jina AI |
| Jina RPM Limit | `JINA_EMBEDDING_RPM_LIMIT` | `120` | Giới hạn Request/phút cấu hình cho Jina |
| Jina TPM Limit | `JINA_EMBEDDING_TPM_LIMIT` | `100000` | Giới hạn Tokens/phút cấu hình cho Jina |
| Jina Batch Chunks | `JINA_EMBEDDING_MAX_CHUNKS_PER_BATCH` | `50` | Số chunk tối đa gửi sang Jina trong một batch |
| Jina Batch TPM Budget | `JINA_EMBEDDING_TPM_BUDGET_PER_BATCH` | `25000` | Ngân sách token an toàn cho một batch Jina |

### 5.2. Two-Stage Retrieval Parameters

| Tham số | Biến trong `config.py` | Giá trị | Vai trò trong Pipeline |
| :--- | :--- | :--- | :--- |
| Dense Top-K | `RAG_DENSE_SEARCH_TOP_K` | `20` | Số lượng ứng viên trích xuất từ chỉ mục HNSW vector cosine |
| Sparse Top-K | `RAG_SPARSE_SEARCH_TOP_K` | `20` | Số lượng ứng viên trích xuất từ chỉ mục GIN tsvector không dấu |
| RRF Constant $k$ | `RAG_RRF_K` | `60.0` | Hằng số làm mượt thứ hạng trong công thức Reciprocal Rank Fusion |
| Candidate Pool | `RAG_RRF_POOL_SIZE` | `15` | Số ứng viên lấy từ RRF đưa vào tầng Reranker chấm điểm lại |
| Reranker Model | `JINA_RERANK_MODEL` | `"jina-reranker-v2-base-multilingual"` | Mô hình Cross-Encoder đa ngữ của Jina AI |
| Final Top-N | `RAG_RERANK_TOP_N` | `5` | Số chunk tinh túy nhất sau Rerank đưa vào ghép nối ngữ cảnh |
| Max Context Tokens | `RAG_CONTEXT_MAX_TOKENS` | `3000` | Ngân sách token tối đa nạp vào System Instruction của LLM |

### 5.3. Quota & Subscription Limits

| Gói cước (Tier) | Hạn mức Nguồn / Sổ tay | Hạn mức Quiz / Sổ tay | Đơn giá niêm yết |
| :--- | :---: | :---: | :--- |
| **Gói Miễn phí (FREE)** | **8 nguồn** (`FREE_MAX_SOURCES`) | **10 bài** (`FREE_MAX_ARTIFACTS`) | Miễn phí trọn đời |
| **Gói Nâng cao (PRO)** | **20 nguồn** (`PRO_MAX_SOURCES`) | **20 bài** (`PRO_MAX_ARTIFACTS`) | 49.000 VNĐ / 30 ngày (`PRO_PLAN_PRICE`) |

---

# 6. Technology Stack

### Backend
* **Web Framework:** FastAPI, Uvicorn, Pydantic v2, Pydantic Settings v2.
* **Database & ORM:** PostgreSQL 16 (`pgvector/pgvector:pg16`), SQLAlchemy 2.0 (async/sync driver `psycopg`), JSONB metadata.
* **Object Storage:** MinIO Python SDK (tách biệt client gọi nội bộ Docker và client ký Presigned URL public).
* **Document Processing:** LibreOffice headless (`soffice`), Cloudmersive API, `pypdfium2`.
* **AI & NLP:** Google GenAI SDK (`google-genai`), Jina AI REST API (Embeddings v3 & Reranker v2), `llama-index-core` (`SentenceSplitter`), `underthesea` (tách câu tiếng Việt).
* **LLMOps & Resilience:** `langfuse>=4.x` (tự động nhận diện v4 SDK và v2/v3 fallback), Tenacity Retry.
* **Security & Payment:** Argon2id (`pwdlib`), PyJWT, HMAC-SHA512 (VNPay integration).

### Frontend
* **Core:** React 19, TypeScript, Vite 8, Tailwind CSS v3.
* **Routing & State:** React Router v7, TanStack Query v5.
* **Form & Interaction:** react-hook-form, react-hot-toast, framer-motion (Page transitions & Skeleton loading).
* **Media & Rich Text:** react-markdown, KaTeX (`katex`, `rehype-katex`, `remark-math`), `@react-oauth/google`.
* **Streaming:** `@microsoft/fetch-event-source` và Fetch API `ReadableStream`.

---

# 7. Current Project Structure

```text
knowledge-sharing-platform/
├── backend/
│   ├── app/
│   │   ├── api/                 # Endpoints: auth, health, config, departments, majors, subjects, documents, notebooks, payments
│   │   ├── core/                # config.py (Pydantic Settings), database.py, security.py, observability.py (Langfuse)
│   │   ├── models/              # base, enums, user, department, major, subject, document, notebook, asset, asset_embedding, notebook_chat, artifact, payment
│   │   ├── schemas/             # Pydantic validation schemas theo từng domain (bao gồm payment, artifact, auth...)
│   │   ├── services/            # auth, department, major, subject, document, asset, storage, startup, notebook, artifact, quiz, quota_service, payment_service
│   │   │                        # (ingestion_service, retrieval_service, notebook_chat_service đóng vai trò re-export proxy)
│   │   ├── rag/                 # Kiến trúc module hóa AI RAG Core:
│   │   │   ├── ingestion/       # splitter.py (LlamaIndex + underthesea), embeddings.py (Strategy: Gemini/Jina, RateLimiter), pipeline.py (Deduplication, Batching)
│   │   │   ├── retrieval/       # retriever.py (Two-Stage RRF + Stitching + Budget), reranker.py (Jina Reranker v2 + NoOp fallback)
│   │   │   └── chat/            # service.py (Condensation, Sliding Window, SSE Streaming Engine)
│   │   ├── main.py, seed.py, seed_data.py
│   ├── scripts/                 # seed_data.py (CLI seed admin/demo), reingest_demo.py (CLI re-ingest Sentence-aware & Jina)
│   ├── tests/                   # 12 test suites backend + evaluation Ragas framework
│   │   ├── evaluation/          # eval_ragas.py, golden_testset.json ([TODO] placeholder)
│   │   ├── conftest.py          # File fixture (hiện tại rỗng 0 bytes)
│   │   └── test_*.py            # test_chat_sse, test_condensation, test_conversion, test_embeddings, test_hybrid_search,
│   │                            # test_ingestion_dedup, test_ingestion_pipeline, test_notebook_artifact, test_notebook_chat,
│   │                            # test_payments, test_quiz_generation, test_reranker
│   ├── alembic/                 # Scaffold Alembic (không sử dụng runtime, DB dùng Base.metadata.create_all)
│   ├── Dockerfile, requirements.txt, .env.example
├── frontend/src/
│   ├── api/                     # apiClient (Axios), getApiErrorMessage
│   ├── components/ui/           # Button, Input, Modal, Spinner, ErrorMessage, PaginationBar, Badge, Breadcrumb, Card
│   ├── components/              # AdminNavLinks, ProtectedRoute, AdminRoute, PageTransition
│   ├── features/
│   │   ├── auth/                # AuthContext, AuthForm, api
│   │   ├── documents/           # hooks, components (PublicResourceCard, PdfPreviewModal), api
│   │   ├── notebooks/           # hooks, components (NotebookCard, NotebookChatPanel, NotebookCreationsHub, QuizRunner/), api
│   │   ├── payments/            # api, components (PricingModal)
│   │   └── taxonomy/            # hooks, DepartmentMajorSubjectPicker, SubjectSearchInput, api
│   ├── layouts/                 # PublicLayout, AppLayout, AdminLayout
│   ├── pages/                   # Home, Departments, DepartmentDetail, MajorDetail, SubjectDetail, DocumentDetail,
│   │                            # Login, Register, MyNotebooksPage, NotebookDetailPage, PaymentReturnPage, AdminTaxonomyPage
│   ├── router/AppRouter.tsx
├── init-db/01-enable-pgvector.sql
├── docs/, docker-compose.yml, .env.example
```

---

# 8. Current API Endpoints & Routes Registry

### 8.1. Backend REST API Endpoints

* **Hệ thống & Cấu hình:**
  * `GET /health`: Kiểm tra trạng thái sống của dịch vụ backend.
  * `GET /config/upload`: Cung cấp cấu hình giới hạn upload cho frontend (Single Source of Truth).
* **Xác thực (`/auth`):**
  * `POST /auth/register`: Đăng ký tài khoản người dùng mới.
  * `POST /auth/login`: Đăng nhập lấy access token OAuth2 (form-data).
  * `GET /auth/me`: Lấy thông tin tài khoản hiện tại, vai trò và hạn mức quota.
  * `POST /auth/google`: Đăng nhập/liên kết tài khoản Google OAuth 2.0.
* **Cơ cấu Đào tạo (`/departments`, `/majors`, `/subjects`):**
  * `GET /departments/`, `GET /departments/{id}` (Admin: `POST`, `PUT`, `DELETE`).
  * `GET /majors/?department_id=`, `GET /majors/{id}` (Admin: `POST`, `PUT`, `DELETE`).
  * `GET /subjects/?major_id=&q=&limit=`, `GET /subjects/{id}` (Admin: `POST`, `PUT`, `DELETE`).
* **Thư viện Tài liệu Công cộng (`/documents`):**
  * `GET /documents/?subject_id=&resource_type=&page=&size=`: Danh sách tài liệu Public có phân trang.
  * `GET /documents/{id}`: Chi tiết tài liệu kèm danh sách tệp đính kèm (`assets`).
  * `GET /documents/{id}/assets/{asset_id}/download`: Cấp presigned URL tải file từ MinIO (15 phút, không cần JWT).
* **Không gian làm việc Sổ tay (`/notebooks` - Yêu cầu JWT):**
  * `POST /notebooks/`: Tạo sổ tay mới.
  * `GET /notebooks/me`: Lấy danh sách sổ tay của tôi kèm số lượng nguồn (`source_count`).
  * `GET /notebooks/{id}`: Chi tiết sổ tay, danh sách nguồn và thông số hạn mức.
  * `PATCH /notebooks/{id}`: Đổi tên tiêu đề sổ tay.
  * `DELETE /notebooks/{id}`: Xóa sổ tay (kích hoạt cascade xóa session, message, artifact).
  * `POST /notebooks/{id}/saved-documents`: Lưu tài liệu thư viện vào sổ tay (kiểm tra quota).
  * `DELETE /notebooks/{id}/saved-documents/{document_id}`: Hủy lưu tài liệu khỏi sổ tay.
  * `POST /notebooks/{id}/assets`: Upload tệp cá nhân vào sổ tay (kiểm tra quota, kích hoạt convert & ingest nền).
  * `DELETE /notebooks/{id}/assets/{asset_id}`: Xóa tệp cá nhân khỏi sổ tay.
  * `GET /notebooks/{id}/assets/{asset_id}/download`: Cấp presigned URL tải tệp cá nhân từ MinIO.
  * `GET /notebooks/{id}/assets/{asset_id}/status`: Polling trạng thái ingestion của asset.
* **Phiên Chat & RAG Stream (`/notebooks/{id}/sessions` - Yêu cầu JWT):**
  * `POST /notebooks/{id}/sessions`: Tạo phiên trò chuyện mới.
  * `GET /notebooks/{id}/sessions`: Lấy danh sách phiên chat trong sổ tay.
  * `PATCH /notebooks/{id}/sessions/{session_id}`: Đổi tên phiên chat.
  * `DELETE /notebooks/{id}/sessions/{session_id}`: Xóa phiên chat.
  * `GET /notebooks/{id}/sessions/{session_id}/messages`: Lấy lịch sử tin nhắn kèm citations.
  * `POST /notebooks/{id}/sessions/{session_id}/chat`: Endpoint chat RAG truyền dữ liệu qua **SSE Stream**.
* **Quiz Studio (`/notebooks/{id}/artifacts` - Yêu cầu JWT):**
  * `POST /notebooks/{id}/artifacts/generate`: Sinh đề trắc nghiệm bằng AI từ danh sách `selected_asset_ids` (kiểm tra quota, cooldown 15s).
  * `GET /notebooks/{id}/artifacts`: Lấy danh sách bài trắc nghiệm đã tạo trong sổ tay.
  * `GET /notebooks/{id}/artifacts/{artifact_id}`: Xem chi tiết câu hỏi và đáp án bài trắc nghiệm.
  * `DELETE /notebooks/{id}/artifacts/{artifact_id}`: Xóa bài trắc nghiệm khỏi sổ tay.
* **Thanh toán & Gói cước (`/payments`):**
  * `POST /payments/create-checkout`: Tạo đơn hàng nâng cấp Pro (49.000đ) và sinh URL thanh toán VNPay (JWT).
  * `GET /payments/vnpay-return`: Nhận redirect từ cổng VNPay, kiểm tra checksum và cập nhật đơn hàng (JWT).
  * `GET /payments/vnpay-ipn`: Webhook Server-to-Server từ VNPay, xử lý idempotency lock và kích hoạt Pro.
  * `GET /payments/orders/{order_code}/status`: Tra cứu trạng thái đơn hàng (JWT, chống IDOR).

### 8.2. Frontend Routes

* **Public Routes:** `/` (Trang chủ), `/login`, `/register`, `/departments`, `/departments/:id`, `/majors/:id`, `/subjects/:id`, `/documents/:id`.
* **Protected Routes (Cần đăng nhập):**
  * `/me/workspace`: Danh sách sổ tay cá nhân (`MyNotebooksPage`).
  * `/me/workspace/:notebookId`: Không gian chi tiết sổ tay, tài liệu, chat RAG và Quiz (`NotebookDetailPage`).
  * `/payment/return`: Trang thông báo kết quả thanh toán VNPay (`PaymentReturnPage`).
* **Admin Routes (Yêu cầu role ADMIN):**
  * `/admin`: *(Redirect tạm thời sang `/admin/taxonomy`)*.
  * `/admin/taxonomy`: Quản lý danh mục Khoa, Ngành, Môn học (`AdminTaxonomyPage`).

---

# 9. Testing Status (Sprint 17)

### 9.1. Backend Test Suite (12 files đang hoạt động)
1. [`test_chat_sse.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_chat_sse.py): Kiểm thử giao thức SSE, thứ tự bắn event (`citations` → `delta` → `done`), xử lý disconnect và concurrency lock.
2. [`test_condensation.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_condensation.py): Kiểm thử logic rút gọn câu hỏi, trượt sliding window 6 tin nhắn, và fast-path bypass cho lượt đầu tiên.
3. [`test_conversion.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_conversion.py): Kiểm thử chuyển đổi DOCX → PDF (Cloudmersive API và LibreOffice subprocess fallback).
4. [`test_embeddings.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_embeddings.py): Kiểm thử `GeminiEmbeddingProvider`, `JinaEmbeddingProvider` (bảo toàn index chunk, MRL 768d), RateLimiter và Factory fallback.
5. [`test_hybrid_search.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_hybrid_search.py): Kiểm thử cô lập dữ liệu theo sổ tay, công thức RRF, adjacent chunk stitching và token budget enforcement.
6. [`test_ingestion_dedup.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_ingestion_dedup.py): Kiểm thử tái sử dụng vector khi trùng SHA-256 hash, không gọi API Gemini/Jina lần 2.
7. [`test_ingestion_pipeline.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_ingestion_pipeline.py): Kiểm thử toàn trình nạp tài liệu từ file PDF sang `AssetEmbedding`.
8. [`test_notebook_artifact.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_notebook_artifact.py): Kiểm thử CRUD artifact, kiểm tra quyền sở hữu sổ tay và trường tính toán `total_items`.
9. [`test_notebook_chat.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_notebook_chat.py): Kiểm thử quản lý phiên chat, quan hệ cascade và tính năng auto-title.
10. [`test_payments.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_payments.py): Kiểm thử khởi tạo đơn hàng VNPay, xác thực chữ ký HMAC-SHA512, Pessimistic Locking chống race condition và Lazy Downgrade quota.
11. [`test_quiz_generation.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_quiz_generation.py): Kiểm thử thuật toán Linspace Sampling, validator JSON Schema câu hỏi và retry decorator.
12. [`test_reranker.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/test_reranker.py): Kiểm thử `JinaRerankProvider` (Top-15 → Top-5), xử lý timeout mạng và fallback sang `NoOpProvider`.

### 9.2. Đánh giá thực nghiệm AI (Ragas Framework)
* **Script:** [`backend/tests/evaluation/eval_ragas.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/evaluation/eval_ragas.py) đánh giá pipeline RAG theo 4 chỉ số: *Faithfulness*, *Answer Relevancy*, *Context Precision*, *Context Recall* sử dụng Gemini làm LLM Judge.
* **Hạn chế hiện tại:** Bộ dữ liệu kiểm thử vàng [`backend/tests/evaluation/golden_testset.json`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/evaluation/golden_testset.json) hiện vẫn chứa các placeholder `[TODO]` cho câu hỏi thực tế và ground truth, cần được gán nhãn dữ liệu chuẩn trước khi chạy benchmark chính thức.
* **File rỗng:** [`backend/tests/conftest.py`](file:///d:/Documents/Visual%20studio%20code/knowledge-sharing-platform/backend/tests/conftest.py) hiện tại có kích thước 0 bytes.

### 9.3. Frontend Testing Status
* **Hiện trạng thực tế:** **Chưa có test tự động (0 file test)**. Frontend chưa được cài đặt các thư viện kiểm thử (như Vitest, Jest, React Testing Library hay Playwright/Cypress); `package.json` hiện chỉ có script `build` và `lint`. Đây là hạn chế kỹ thuật còn tồn đọng của đồ án.

---

# 10. Non-functional Requirements & Constraints (Hạn chế Kỹ thuật)

> Phần này cung cấp dữ liệu thực tế cho mục Hạn chế của đề tài (Chương 3):

* **Giới hạn tệp tin tải lên:** Dung lượng tối đa 30MB/file (`MAX_FILE_SIZE_MB = 30`), chỉ tiếp nhận định dạng PDF và DOCX được xác thực nội dung (magic bytes).
* **Bảo mật tệp tin:** Hiện tại hệ thống chưa tích hợp engine quét virus/mã độc tự động cho các tệp tin người dùng tải lên MinIO.
* **Ngân sách tài nguyên & API:** Là đồ án cá nhân với ngân sách API Gemini và Jina free-tier/giới hạn, hệ thống không chạy các mô hình local nặng do không trang bị GPU máy chủ riêng; do đó phải tối ưu chặt chẽ qua Rate Limiter, Token Budget, và Deduplication.
* **Xử lý tài liệu scan (Scanned PDF):** Hệ thống chưa tích hợp OCR; các tài liệu PDF scan có tổng số ký tự trích xuất dưới 100 ký tự sẽ bị đánh dấu `FAILED` với mã lỗi `SCANNED_DOCUMENT_UNSUPPORTED`.
* **Frontend Testing:** Chưa thiết lập bộ kiểm thử tự động (Unit test / Integration test) cho giao diện người dùng.

---

# 11. Coding Principles

* **Service Layer Architecture:** Tách biệt rõ ràng mối bận tâm (Separation of Concerns). Router chỉ đóng vai trò phân giải request, chứng thực quyền hạn và trả response; 100% nghiệp vụ xử lý nằm ở Service Layer.
* **Clean Code & SRP:** Mỗi function/class đảm nhiệm duy nhất một trách nhiệm (Single Responsibility Principle).
* **Centralized Configuration:** Toàn bộ thông số thuật toán, hạn mức, timeout, model names tập trung tại `Settings` (`config.py`). Tuyệt đối không hardcode magic numbers trong code xử lý.
* **State & Query Key Factory:** Phía Frontend quản lý server-state bằng TanStack Query với query keys tập trung theo feature; action-based custom hooks tách biệt hoàn toàn khỏi component giao diện.

---

# 12. Idea Backlog / Tồn đọng Kỹ thuật Thực tế

### 12.1. Nợ kỹ thuật tồn đọng cần xử lý
* **Frontend Test Suite:** Thiết lập Vitest và React Testing Library để bổ sung unit test cho các luồng giao diện trọng yếu (`useNotebookChatStream`, `QuizRunner`, `PricingModal`).
* **Golden Testset Ragas:** Hoàn thiện bộ câu hỏi và đáp án mẫu trong `golden_testset.json` từ tài liệu môn học demo thật để xuất báo cáo đánh giá định lượng năng lực RAG.
* **Xử lý ID Route không hợp lệ:** Chuẩn hóa ngoại lệ trả về khi path parameter không phải số hoặc bản ghi không tồn tại.
* **Chuẩn hóa i18n:** Rà soát và chuyển đổi đồng bộ các enum tiếng Anh còn sót lại trên giao diện sang nhãn tiếng Việt thân thiện.

### 12.2. Hướng phát triển mở rộng trong tương lai
* **Quản trị Người dùng & Gói cước (Admin CRUD Users & Quota - Đang cân nhắc):** Xây dựng trang Admin quản lý tài khoản người dùng:
  * Xem danh sách toàn bộ user, trạng thái tài khoản, gói cước hiện tại (`FREE`/`PRO`), và thời điểm hết hạn `pro_expires_at`.
  * Cho phép Admin điều chỉnh thủ công tier của user (gán `PRO` thủ công để phục vụ test tính năng/demo mà không cần thanh toán thật qua VNPay Sandbox mỗi lần, hoặc revert về `FREE`).
  * Xem nhanh thông số usage cơ bản (số nguồn tài liệu và bài quiz đang sử dụng so với hạn mức quota) bằng cách tái sử dụng `quota_service.py` có sẵn mà không cần dựng thêm hạ tầng.
  * *Đánh giá kỹ thuật:* Rủi ro thấp nhất vì chỉ thao tác trên model `User` và service có sẵn, hoàn toàn độc lập với core AI pipeline (retrieval/chat/quiz). Triển khai sau khi hoàn thành báo cáo nếu còn thời gian.
* **Mở rộng định dạng tệp:** Hỗ trợ nạp bài giảng dạng trình chiếu PowerPoint (`.pptx`) thông qua LibreOffice headless converter đã có sẵn.
* **RAG Response Caching:** Thiết lập bộ nhớ đệm câu trả lời cho các câu hỏi phổ biến trùng lặp nhằm tiết kiệm chi phí gọi LLM.
* **Chat AI Agent Tool Calling:** Tích hợp Function Calling cho Gemini trong phiên chat, cho phép người dùng ra lệnh bằng ngôn ngữ tự nhiên để kích hoạt sinh trắc nghiệm ngay trong luồng đàm thoại.
* **Nhánh duyệt tài liệu trực tuyến (Document Moderation):** *Đã đưa vào Backlog mở rộng sau tốt nghiệp.* Tài liệu công cộng tiếp tục được đưa vào qua kênh Google Forms và seed script nhằm tinh gọn phạm vi và tránh rủi ro kiểm duyệt.

---

# 13. Development Workflow & Git Convention

* **Workflow:** Planning → Implementation → Verification / Testing → Documentation Update → Commit & Push.
* **Git Commit Convention:** Đặt commit message có ý nghĩa theo dạng `feat:`, `fix:`, `refactor:`, `docs:`, `test:`. Tránh các commit chung chung như `update` hay `fix bug`.
* **AI Collaboration:** Luôn đọc và kiểm chứng mã nguồn thực tế trước khi cập nhật tài liệu hoặc đưa ra nhận định; không mô tả tính năng kế hoạch là đã hoàn thành.
