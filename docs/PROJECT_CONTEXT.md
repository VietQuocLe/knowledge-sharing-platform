# PROJECT_CONTEXT.md

# Knowledge Sharing Platform

> Graduation Project — AI-powered Knowledge Sharing Platform inspired by Studocu + NotebookLM

---

# 1. Project Overview

## Description

Knowledge Sharing Platform là hệ thống chia sẻ học liệu kết hợp AI. Mục tiêu là xây dựng nền tảng tổ chức học liệu theo Khoa → Ngành → Môn học, cho phép người dùng tạo resource cá nhân, upload tài liệu và đưa tài liệu qua quy trình kiểm duyệt để chia sẻ công khai. AI/RAG và notebook cá nhân là các phase tiếp theo.

---

# 2. Current Progress

**Top of mind / Định hướng phát triển gần:**
Hệ thống tiếp tục theo mô hình sprint "vertical slice" (hoàn thiện cả Frontend + Backend trong cùng một sprint), nhưng từ giai đoạn AI/RAG trở đi sẽ **tách lộ trình thành các sprint độc lập nhỏ hơn**. Sprint 11 đã hoàn thiện trang chi tiết Notebook, lưu tài liệu công khai và upload tệp cá nhân. Trước khi bước vào pipeline AI, hệ thống dừng lại một nhịp ở **Sprint 11.5 — Document Conversion & Preview Debt Cleanup** để trả nợ kỹ thuật phần xem trước tài liệu (DOCX chưa preview được, luồng preview/download chưa thống nhất), chuẩn hóa mọi tài liệu DOCX sang PDF phái sinh để làm đầu vào đồng nhất cho Ingestion Pipeline ở Sprint 12.

**Lý do tách nhỏ lộ trình AI/RAG:**
Theo đúng pattern đã áp dụng thành công ở Sprint 11 (phase backend có script test riêng, chạy xanh trước rồi mới làm UI), mỗi sprint AI sẽ **tự kiểm thử độc lập trước khi chuyển sang sprint kế tiếp**. Cách này tránh việc chồng nhiều tầng (ingestion + retrieval + LLM + UI) trong cùng một sprint, vốn rất khó debug, khó xác định tầng nào gây lỗi và gần như không thể rollback từng phần.

Current Sprint

> 🔄 Sprint 17 — Testing — đang triển khai

Overall Progress

99%

Status

✅ Sprint 5 Completed
✅ Sprint 6 Completed
✅ Sprint 7 Completed
✅ Sprint 8 Completed
✅ Sprint 8.5 — Database Architecture Refactor — **hoàn thành**
✅ Sprint 9 — UI/UX Polish & Design Consistency — **hoàn thành**
✅ Sprint 10 — Notebook (AI Workspace) Feature — Dashboard + Layout Redesign — **hoàn thành**
✅ Sprint 10.5 — Notebook Dashboard Actions (Rename/Delete) — **hoàn thành**
✅ Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload — **hoàn thành**
✅ Sprint 11.5 — Document Conversion & Preview Debt Cleanup — **hoàn thành**
✅ Sprint 12 — Ingestion Pipeline (Backend only) — hoàn thành
✅ Sprint 13 — Retrieval Engine & Chat API (Backend only) — **hoàn thành**
✅ Sprint 14 — Chat Frontend & Citation UI — **hoàn thành**
✅ Sprint 15 — Quiz Studio (Backend) — **hoàn thành**
✅ Sprint 16 — Quiz Studio (Frontend) — **hoàn thành**
✅ Sprint 16.5 — Tối ưu hóa Tầng Service, LLM Observability & Hoàn thiện Trải nghiệm (Hardening) — **hoàn thành**
✅ Sprint 16.6 — Centralized Settings & LLMOps Observability Hardening — **hoàn thành**
🔄 Sprint 17 — Testing — **đang triển khai**
⏳ Sprint 18 — Deployment & Optimization — **kế hoạch**

---

# 3. Current Sprint Goal

**Sprint 17 — Testing (Đang triển khai):**
Xây dựng và hoàn thiện bộ test tự động cho toàn bộ hệ thống (Unit tests, Integration tests, End-to-end user flows) và kiểm thử chất lượng giao diện người dùng.

Mục tiêu chi tiết:
- **Backend Testing:** Tăng độ phủ kiểm thử cho các service trích xuất, embedding, hybrid search, RAG stream và artifacts generation.
- **Frontend Testing:** Kiểm thử dòng chảy trò chơi trắc nghiệm, chat AI, và liên kết tài liệu.

## Đặc tả kỹ thuật Sprint 11.5

### 1. Hạ tầng Docker

- Cài `libreoffice-writer` (và font tiếng Việt) trong `backend/Dockerfile` để có binary `soffice` chạy headless.
- Lệnh convert chạy trong thư mục tạm, có timeout, không dùng `shell=True`:

```text
soffice --headless --norestore --convert-to pdf --outdir <tmpdir> <input.docx>
```

- Mỗi lần convert dùng một `-env:UserInstallation` riêng trong thư mục tạm để tránh xung đột profile khi có nhiều request đồng thời.

### 2. Model & Schema

- `Asset` thêm cột `converted_pdf_path: Mapped[str | None]` (nullable) — object key của bản PDF phái sinh trên MinIO.
- File gốc (`file_path`) **không bị thay thế**: DOCX gốc vẫn là bản dùng để tải về; PDF phái sinh chỉ phục vụ preview và (từ Sprint 12) trích xuất text.
- Bản PDF phái sinh lưu cùng bucket, theo quy ước key `derived/{asset_id}.pdf`, không tạo thêm bản ghi `Asset` nên **không tính vào quota** `MAX_SOURCES_PER_NOTEBOOK = 10`.
- Schema trả về cho frontend bổ sung cờ suy ra từ dữ liệu (ví dụ `is_previewable = file_type == PDF or converted_pdf_path is not None`) thay vì hardcode theo đuôi file.

### 3. `conversion_service.py`

- Vị trí: `backend/app/services/conversion_service.py`, chỉ nhận `asset_id` và tự mở `db_session` riêng khi chạy nền.
- Luồng: tải file gốc từ MinIO → ghi ra thư mục tạm → gọi `soffice` → upload PDF kết quả lên MinIO → cập nhật `converted_pdf_path` → dọn thư mục tạm (`finally`).
- Bọc toàn bộ trong `try/except`: convert lỗi (file hỏng, timeout, `soffice` trả non-zero) chỉ log lại và để `converted_pdf_path = NULL`, **không làm hỏng upload** đã thành công.
- Kích hoạt qua FastAPI `BackgroundTasks` ngay sau khi upload trả `201`, giữ đúng triết lý best-effort đã dùng ở Sprint 10.5/11.

### 4. Preview & Download

- Endpoint preview trả presigned URL của `converted_pdf_path` nếu có, ngược lại trả `file_path` (PDF gốc).
- Endpoint download **luôn** trả file gốc để giữ đúng định dạng người dùng đã tải lên.
- Frontend: bỏ điều kiện chặn cứng theo đuôi file, bật nút "Xem trước" cho DOCX ở cả thẻ nguồn trong `NotebookDetailPage` lẫn thư viện tài liệu Public; khi PDF phái sinh chưa sẵn sàng thì hiển thị trạng thái đang xử lý thay vì lỗi.

---

# 4. Completed

> Phần này mô tả code **đã thực sự tồn tại trong repo** tính đến hết Sprint 10.

## Backend

- Backend foundation, config, database connection, FastAPI lifespan và Health API
- Authentication: register, OAuth2 password login, Argon2id password hashing và JWT Bearer
- Default admin được tạo khi app khởi động
- Department, Major, Subject CRUD; GET public, ghi dữ liệu admin-only
- Sprint 5 upload: PDF/DOCX validation và lưu Asset trong MinIO
- Seed script idempotent có Document mẫu
- **Sprint 7 (backend phát sinh):**
  - `GET /majors/?department_id=`, `GET /subjects/?major_id=`
  - `GET /resources/admin`; service `get_owned_by_id`
- **Sprint 8.5 — Database Architecture Refactor:**
  - Models: `Document`, `Notebook`, `NotebookSavedDocument`, `Asset` (bỏ `resource_id`, thêm `document_id`/`notebook_id`); `AssetEmbedding` placeholder
  - Enums: `DocumentStatus` (DRAFT/PUBLIC/DELETED), `ResourceType` (EXAM/SLIDE/DOCUMENT/LECTURE/REFERENCE/SYLLABUS/VIDEO/AUDIO/LINK/AI_ARTIFACT)
  - API `/documents/`: `GET /documents/` (paginated, filter subject_id + resource_type), `GET /documents/{id}`, `GET /documents/{id}/assets/{assetId}/download` (presigned MinIO URL, 15 phút)
  - `storage_service.get_presigned_download_url()` hoạt động
  - `document_service.py`, `asset_service.py` — business logic tách khỏi router
  - Model cũ `Resource` đã xóa hoàn toàn
- **Sprint 9 — UI/UX Polish & Design Consistency:**
  - Tích hợp API tìm kiếm môn học (`GET /subjects/?q=...`) hỗ trợ tìm kiếm không phân biệt dấu tiếng Việt (ILike query).
  - Cập nhật idempotent seed script (`seed.py`) để chèn Document mẫu và chèn file tài liệu PDF thực tế (`KTLT_Chapter1_nDArray.pdf`) vào MinIO cho chế độ kiểm thử / validation.
- **Sprint 10 — Notebook (AI Workspace) Feature — Dashboard + Layout Redesign:**
  - Model `Notebook`: thêm cập nhật tự động `updated_at` (với `onupdate=func.now()`).
  - Schemas: Định nghĩa `NotebookCreate` (title bắt buộc, subject_id nullable) và `NotebookRead`.
  - Service Layer: Cấu trúc tối ưu hàm `get_notebooks_by_owner()` thông qua LEFT OUTER JOIN với bảng `Subject` và hai bảng subquery đếm `Asset` + `NotebookSavedDocument` để trả về `source_count` chính xác, phòng tránh lỗi N+1.
  - Endpoints: `POST /notebooks/` và `GET /notebooks/me` đi kèm bảo vệ định danh người dùng qua JWT.
  - *Lưu ý cho sprint sau:* khi thêm các route chi tiết như `GET /notebooks/{notebook_id}`, phải khai báo route `/me` TRƯỚC `/{notebook_id}` trong router, tránh FastAPI match nhầm "me" là một path parameter ID.
- **Sprint 10.5 — Notebook Dashboard Actions (Rename/Delete):**
  - Tích hợp schema `NotebookUpdate` hỗ trợ PATCH/đổi tên, validation tiêu đề với Pydantic `@field_validator` (trim đầu cuối, required, maxLength 500 ký tự).
  - API endpoints: `PATCH /notebooks/{notebook_id}` và `DELETE /notebooks/{notebook_id}` được bảo vệ qua JWT và kiểm định ownership (403/404 handling).
  - Deletion logic: Sử dụng SQLAlchemy/Postgres `CASCADE` tự động làm sạch các bản ghi trong bảng `Asset` và `NotebookSavedDocument`.
  - Storage sweep: Tận dụng FastAPI `BackgroundTasks` để thực thi việc xóa vật lý các tập tin Asset MinIO ngầm một cách không cản trở (best-effort).
  - API `GET /notebooks/{notebook_id}/assets/{asset_id}/download` để cấp presigned URL tải tệp tin MinIO trực tiếp.

- **Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload — hoàn thành:**
  - Cấu hình hạn mức số lượng nguồn gộp chung `MAX_SOURCES_PER_NOTEBOOK = 10` trong project settings.
  - API `GET /notebooks/{notebook_id}` để trả về cấu trúc chi tiết của Sổ ghi chú bao gồm thông số đếm và danh sách nguồn tài liệu.
  - API liên kết tài liệu `POST /notebooks/{notebook_id}/saved-documents` và hủy liên kết `DELETE /notebooks/{notebook_id}/saved-documents/{document_id}` bảo vệ bằng JWT và xác thực sở hữu.
  - API tải tập tin cá nhân `POST /notebooks/{notebook_id}/assets` và xóa tập tin `DELETE /notebooks/{notebook_id}/assets/{asset_id}` với kiểm định nội dung file (magic bytes để chặn file giả mạo PDF/DOCX) và giới hạn 30MB.
  - Khởi động dọn dẹp vật lý file trong MinIO ngầm thông qua FastAPI `BackgroundTasks` khi xóa Asset.
  - API `GET /notebooks/{notebook_id}/assets/{asset_id}/download` để cấp presigned URL tải tệp tin MinIO trực tiếp.

- **Sprint 11.5 — Document Conversion & Preview Debt Cleanup:**
  - Cài đặt `libreoffice-writer` và bộ fonts tiếng Việt trong Dockerfile của Backend.
  - Thêm cột `converted_pdf_path` và `conversion_status` (PENDING, COMPLETED, FAILED) vào bảng `assets`.
  - Triển khai `conversion_service.py` xử lý chuyển đổi DOCX sang PDF thông qua headless `soffice` ở chế độ lập profile riêng biệt độc lập, chạy trên background worker của FastAPI.
  - Cho phép các route download/preview tự động ưu tiên PDF phái sinh, giải quyết triệt để lỗi `SignatureDoesNotMatch` của MinIO nhờ dùng một client MinIO public chuyên biệt ký presigned URL trực tiếp.
  - Cập nhật frontend mở khóa xem trước cho định dạng `.docx`, hiển thị huy hiệu dynamic trạng thái xử lý/lỗi và nút "Tải về" file gốc luôn hoạt động.

- **Sprint 12 — Ingestion Pipeline (Backend only):**
  - Schema & DB: Bổ sung extension `unaccent` và wrapper `immutable_unaccent()`; tạo bảng `asset_embeddings` (`id`, `asset_id` CASCADE, `chunk_index`, `content`, `embedding VECTOR(768)`, `tsv_content` Generated Column TSVECTOR không dấu, `page_number`, `metadata_`); thiết lập index HNSW (`vector_cosine_ops`) và index GIN trên `tsv_content`; cập nhật bảng `assets` với `file_hash`, `ingestion_status`, `ingestion_error`, `chunk_count`.
  - Ingestion Core: Xây dựng `ingestion_service.py` tích hợp `pypdfium2` trích xuất text độc lập từng trang (page-aware chunking 500-700 tokens, 100 tokens overlap trong cùng trang); Scanned Guard (< 100 ký tự -> `SCANNED_DOCUMENT_UNSUPPORTED`); cơ chế idempotent tự dọn chunk cũ; batch embedding qua Google GenAI SDK (`google-genai`, `gemini-embedding-001`, 768d, `RETRIEVAL_DOCUMENT`) bọc Tenacity retry.
  - Wiring: Tự động kích hoạt tác vụ ngầm qua FastAPI `BackgroundTasks` khi upload PDF; nối chuỗi đồng bộ sau khi convert DOCX thành công trong `conversion_service.py` (chuyển `FAILED`/`CONVERSION_FAILED` nếu lỗi).
  - API & Seeding: Cung cấp endpoint polling `GET /notebooks/{notebook_id}/assets/{asset_id}/status` có JWT & Ownership Guard; cập nhật `seed.py` với cờ `--ingest` (mặc định bỏ qua để tiết kiệm quota API).
  - Kiểm thử: Bộ test độc lập `test_ingestion_pipeline.py` và các script verify chạy xanh 100% trên Docker.

- **Sprint 13 — Retrieval Engine & Chat API (Backend only — Hoàn thành):**
  - Chat Persistence: Thiết lập quan hệ database cascades cho `NotebookChatSession` và `NotebookChatMessage` với default message ordering, ownership guards, và auto-titling thông qua background worker (Gemini).
  - Retrieval Engine: Triển khai Hybrid Search RRF kết hợp Dense (cosin distance, HNSW index m=16, ef=64) và Sparse (GIN ts_rank_cd không dấu), scoped retrieval, adjacent chunk stitching, token budget enforcement (3000 tokens) sử dụng Gemini count_tokens API.
  - Intent Routing & Query Condensation: Tích hợp lời gọi LLM rút gọn câu hỏi và phân tách ý định (needs_rag) sử dụng structured response schema, sliding window (6 tin nhắn), first-turn fast-path bypass, tenacity retry (3 attempts) và safe fallback default values.
  - SSE Streaming & Concurrency: Phát triển API `/chat` dạng SSE, concurrency locks (409 Conflict), xử lý ngắt kết nối (discard/abort stream), và cơ chế write-on-complete nguyên tử.
  - Kiểm thử: Xây dựng các test suites `test_hybrid_search.py`, `test_condensation.py`, `test_chat_sse.py`, `test_notebook_chat.py` xác minh chính xác dữ liệu cô lập, RAG flows, chit-chat, và concurrency control.
  - **Backend Bug Fixes (ngoài phạm vi FE, do người sử dụng yêu cầu khi test Phase 2, không phải agent tự mở rộng):**
    - `notebook_chat_service.py`: Loại bỏ hardcode `needs_rag=True` ở lượt chat đầu tiên, thay thế bằng lời gọi đánh giá thực tế từ Gemini và fallback kiểm soát số lượng từ (gửi ≤3 từ mặc định `needs_rag = False`).
    - `ingestion_service.py`: Tăng thời gian cooldown của decorator retry `wait_exponential(multiplier=2, min=4, max=50)` giúp chịu được khoảng thời gian cooldown 42 giây khi gặp giới hạn Gemini 429. Nâng kích số batch từ 15 lên 30 kèm nhịp nghỉ `sleep(1)` giữa các batch, đồng thời thực thi truy vấn lại đối tượng `Asset` sau khi gọi rollback để tránh phát sinh lỗi `ObjectDeletedError`.
- **Sprint 15 — Quiz Studio (Backend) — hoàn thành:**
  - **Data Model**: Thêm model `NotebookArtifact` (bảng `notebook_artifacts`, denormalize `user_id` tăng hiệu năng truy vấn phân quyền, khóa ngoại CASCADE với `Notebook`), enum `ArtifactType` (QUIZ, FLASHCARD, SUMMARY) và cấu hình mapping alias an toàn `metadata_` -> `metadata`.
  - **Pydantic Schemas**: Thiết kế các schema `QuizOption`, `QuizQuestion` (kèm validator `@model_validator` loại bỏ options trùng key A-D), `QuizContentPayload`, `QuizGenerateRequest`, `ArtifactSummaryResponse` (computed `total_items` từ metadata, tránh lazy load) và `ArtifactDetailResponse`.
  - **Validation Pipeline 4 lớp**: Ownership Guard (kiểm quyền Notebook/User) → Cooldown Guard 15s (tránh nhấn đúp API) → Quota Guard 20 artifacts (hạn mức Sổ tay) → All-or-Nothing Asset Completed Check (chỉ sinh khi tài liệu đã thuộc Sổ tay và ingest COMPLETED).
  - **Linear Space Sampling & Context Extraction**:
    - Query JOIN tối ưu giữa `AssetEmbedding` và `Asset` để gom text chunks trong một truy vấn duy nhất.
    - Thuật toán *Multi-Asset Linear Space Sampling* (Numpy-style Linspace) nội suy khoảng cách đều theo công thức `index = round(i * (total_chunks - 1) / (budget_per_asset - 1))`, đảm bảo bao phủ 100% biên tài liệu (luôn lấy trọn vẹn cả chunk mở đầu `index = 0` và chunk kết luận `index = N - 1`), triệt tiêu hoàn toàn hiện tượng undershoot/bỏ sót nội dung cuối tài liệu.
    - Định dạng prompt context chuẩn hóa: `[Tài liệu: {file_name} - Trang {page_number}]`.
  - **Core GenAI Structured Output**:
    - Xây dựng pure function `_call_gemini_with_retry` bọc Tenacity exponential retry (`stop_after_attempt(3)`, wait `2-10s`).
    - Tích hợp model `gemini-3.1-flash-lite`, truyền `response_schema=QuizContentPayload` định dạng JSON.
    - Soạn System Instructions chuẩn Bloom (30% hiểu/nhận biết, 70% vận dụng/suy luận logic) và ràng buộc chống bịa đặt dữ liệu (anti-hallucination).
  - **API Endpoints & I/O Optimization**:
    - Cấp 4 route CRUD/generate artifacts.
    - Sử dụng `defer(NotebookArtifact.content)` và before validator trong Pydantic schema giải quyết triệt để lỗi xung đột thuộc tính `Base.metadata` của SQLAlchemy, đồng thời ngăn chặn lazy load dữ liệu JSONB lớn không mong muốn.
  - **Kiểm thử**: Viết `backend/tests/test_quiz_generation.py` phủ unit test sampling, Pydantic validator và integration test Mock Gemini API thành công 100%.


## Frontend

- **Sprint 6 — FE Foundation:** Vite/React/TS/Tailwind, routing, API client, AuthContext, layout/navigation, login/register, ProtectedRoute/AdminRoute
- **Sprint 7 — FE Catch-up Features:** TanStack Query v5, browse public flow, personal resources, upload/submit-review, admin moderation & taxonomy, query key factory, cache invalidation
- **Sprint 8 — Code Structure Refactor:** Action-based hooks, DepartmentMajorSubjectPicker, upload config API, error handling, barrel exports
- **Sprint 8.5 — Frontend Cleanup:**
  - `features/resources/api.ts`: types mới `Document`/`Asset`/`DocumentPageResponse`; 3 active API calls (`getDocumentList`, `getDocumentDetail`, `getAssetDownloadUrl`); old APIs commented
  - `features/resources/queryKeys.ts`: `documentsKeys` root `['documents']`; backwards-compat alias `resourcesKeys`
  - Hooks mới: `useDocuments`, `useDocumentDetail`
  - Hooks write/admin cũ: stubbed (giữ trong repo, không export)
  - `PublicResourceCard`: nhận `Document` prop, link `/documents/:id`
  - `SubjectDetailPage`, `ResourceDetailPage` (+ nút Tải về presigned): cập nhật sang Document API
  - `MyResourcesPage`: temp notice (no `/resources/me` API)
  - `ResourceCreatePage`, `ResourceUploadPage`, `AdminModerationPage`: stubbed (`return null`)
  - `AppRouter`: routes cũ commented, alias `/documents/:id` thêm vào; `/admin/taxonomy` giữ active
  - Nav links "Đóng góp tài liệu" ẩn ở `PublicLayout`, `AppLayout`, `HomePage`
  - `npm run build` ✅ exit code 0
- **Sprint 9 — UI/UX Polish & Design Consistency:**
  - Tách và dọn dẹp features: đổi tên thư mục `features/resources/` thành `features/documents/` và gỡ bỏ hoàn toàn các hook/file legacy không còn sử dụng.
  - Tạo các component UI dùng chung chuẩn hóa: `Badge`, `Breadcrumb`, `Card`, `EmptyState` tại `src/components/ui/`.
  - Triển khai định dạng localized translations tiếng Việt (`src/utils/formatters.ts`) cho resource types, document status, và relative times.
  - Tích hợp ô tìm kiếm môn học tức thì (`SubjectSearchInput`) được debounced vào Navbar trong `PublicLayout` và `AppLayout`.
  - Triển khai `PdfPreviewModal` cho phép hiển thị trực tiếp file PDF bằng iframe từ CDN presigned URL (15 phút).
  - Hoàn thiện luồng duyệt Progressive Disclosure:
    - `HomePage`: thay TaxonomyView bằng lưới card Khoa (Department) và thanh tìm kiếm nhanh cùng nút đóng góp qua Google Form.
    - `DepartmentDetailPage`: hiển thị danh sách Ngành trực thuộc dạng card.
    - `MajorDetailPage`: hiển thị chuyên đề Môn học theo khối kiến thức dưới dạng accordion nhóm.
    - `SubjectDetailPage`: thay thế card tài liệu bằng danh sách flat hàng ngang gọn nhẹ, cho phép tải/xem trực tiếp.
    - `DocumentDetailPage`: trang chi tiết tài liệu hỗ trợ PDF preview và nút tải về.
  - Hoàn thành responsive navbar với hamburger toggle menu cho mobile devices.
  - `npm run build` ✅ hoạt động bình thường, không gặp lỗi import/type.
- **Sprint 10 — Notebook (AI Workspace) Feature — Dashboard + Layout Redesign:**
  - Cấu trúc thư mục mới `features/notebooks` tương tự `features/documents` bao gồm `api.ts`, `queryKeys.ts`, custom hooks (`useNotebooks`, `useCreateNotebook`).
  - Components: `NotebookCard` (hiển thị thời gian cập nhật tương đối bằng formatRelativeTime, icon BookOpen / Sparkles tương ứng trạng thái liên kết môn học, số lượng tài liệu, không hiện tag môn học để các card luôn đồng bộ chiều cao tránh lệch khối), `CreateNotebookCard` (trigger nét đứt), `CreateNotebookModal` (sử dụng autocomplete tìm kiếm môn học).
  - MyNotebooksPage: đón chào sinh động "Chào buổi sáng/chiều/tối" bằng giờ thực tế máy khách, lọc danh sách local không cần gọi API phụ và hỗ trợ các trạng thái rỗng `EmptyState`.
  - Chỉnh sửa hệ thống layout: chuyển đổi toàn bộ `PublicLayout` & `AppLayout` từ Topbar ngang sang Dark Sidebar cố định trái (logo, nav, CTA đóng góp), di chuyển ô tìm kiếm môn học và cụm thông tin đăng nhập lên phần `<main>` (không nằm trong sidebar).
  - Đã tối giản Sidebar chỉ còn "Trang chủ", "Workspace cá nhân" (+ "Quản trị" nếu là admin), lược bỏ "Khám phá Khoa/Ngành" hoàn toàn vì trùng lặp.
  - Ẩn tự động ô tìm kiếm môn học chung tại header khi khớp `pathname.startsWith('/me/workspace')`.
  - `npm run build` ✅ hoạt động ổn định và biên dịch hoàn toàn thành công.
- **Sprint 10.5 — Notebook Dashboard Actions (Rename/Delete):**
  - API Client: Thêm cuộc gọi API `renameNotebook` và `deleteNotebook` trong `notebooksApi`.
  - Mutations Hook: Tạo các custom hooks `useRenameNotebook` và `useDeleteNotebook` hỗ trợ invalidate query-cache.
  - Dropdown Menu: Thiết kế Kebab menu (⋮) ở góc phải của `NotebookCard`, ngăn chặn hiện tượng nổi bọt sự kiện (`e.stopPropagation()`) để không kích hoạt điều hướng trang của card Link.
  - Custom Hook: Tự biên soạn `useClickOutside` bằng React/hooks thuần để auto-close dropdown khi click ra ngoài.
  - Modals: Tạo `RenameNotebookModal` và `DeleteNotebookConfirmModal` tách biệt, đồng bộ hóa giới hạn tối đa 500 ký tự cho tiêu đề ở cả hai modal Create/Rename nhằm thống nhất với Backend.
- **Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload:**
  - Tái thiết kế bố cục lồng nhau của `AppLayout.tsx` để cung cấp chế độ cuộn độc lập cho trang tĩnh và chế độ hiển thị tràn 100% viewport (`p-0 overflow-hidden w-full h-full`) cho workspace.
  - Xây dựng layout dòng chia đôi (Split View) trong `NotebookDetailPage.tsx` với Cột trái hiển thị tài liệu (cuộn toàn cột) và Cột phải hiển thị thanh chat AI cao kịch màn hình kết hợp nút bật/tắt (floating toggle) tiện dụng.
  - Thiết kế ô Quick Actions "Bắt đầu học tập" và thanh hạn mức quota Compact Quota Indicator chỉ hiển thị thông báo text dạng `X / 10 nguồn` bên cạnh danh mục tài liệu.
  - Xây dựng component `AddDocumentModal` hỗ trợ Tab thư viện (truy vấn phân trang) và Tab tải lên tệp tin cá nhân (chọn nhiều tệp, upload song song concurrent mutation).
  - Tích hợp Kebab menu hành động trên mỗi thẻ nguồn tài liệu: xem trước PDF, tải file thực tế (download link), điều hướng thư viện công cộng, và xóa/hủy lưu tài liệu.
  - Thêm logic kiểm định `isPreviewable` để chặn xem trước đối với các định dạng không phải PDF (như DOCX) để tránh tự động tải tệp tin ngầm gây lỗi màn hình trắng.
  - Di chuyển các modal Rename/Delete ra ngoài thẻ `<Link>` đè trong `NotebookCard.tsx` để chấm dứt lỗi trắng trang khi invalidate cache.
  - Di chuyển liên kết "Quay lại Workspace" lên trực tiếp thanh Top Bar toàn cục của layout AppLayout (hiển thị động khi khớp luồng chi tiết).
- **Sprint 16 — Quiz Studio (Frontend) — hoàn thành:**
    - **Data Hook Layer:** Triển khai 4 custom hooks quản lý server-state: `useArtifacts`, `useArtifactDetail`, `useGenerateQuiz`, và `useDeleteArtifact` tương tác với các REST endpoints. Hook mutation `useGenerateQuiz` thiết lập cơ chế cache warming qua việc ghi trực tiếp chi tiết bài trắc nghiệm vào cache TanStack Query bằng `setQueryData` và invalidate dữ liệu danh sách creations hub (`invalidateQueries`).
    - **NotebookCreationsHub:** Panel hiển thị danh sách các bài ôn tập AI (Quiz). Tích hợp văn bản hạn mức quota (`X / 20 bài ôn tập`) cạnh tiêu đề, loading spinner và trạng thái rỗng "Kho trống" kèm nút CTA nhanh để kích hoạt modal sinh trắc nghiệm.
    - **GenerateArtifactModal:** Modal cấu hình tạo Quiz. Hỗ trợ checkbox vô hiệu hóa tài liệu chưa xử lý xong (`ingestion_status != COMPLETED`), cấp tùy chọn nhanh số lượng câu hỏi `[5, 10, 15, 20]`, và trạng thái Submit bị khóa (disable backdrop click, cancel, submit và hiển thị loader spinner).
    - **DeleteArtifactModal:** Modal cảnh báo xác nhận xóa vĩnh viễn bài quiz, có cơ chế ngăn tương tác khi đang xóa và mutation invalidation chuẩn xác.
    - **Quiz Runner System:**
      - `QuizRunner`: Component chính đi kèm khung xương skeleton loading nhấp nháy, xử lý lỗi 404 bằng dialog cứu hộ và toast thông minh.
      - `QuizHeader`: Bảng quản lý chứa tiêu đề bài quiz, thông số tiến trình (`Kết quả: X / Y câu`) và nút Reset tiện lợi có icon quay lại.
      - `QuizQuestionItem`: Hiển thị câu hỏi, các lựa chọn A-D độc lập với cơ chế phản hồi chọn lập tức (xanh lá cây nếu đúng, đỏ nếu sai) và hiển thị hộp thoại giải thích nguồn gốc.
    - **Kiến trúc State & URL SearchParams:**
      - Tách biệt và nâng quản lý state `activeArtifactId` lên `NotebookDetailPage.tsx` thông qua hook `useSearchParams` đọc từ query URL `?artifact={id}` giúp đồng bộ hoàn hảo nút quay lại (Back/Forward) của trình duyệt.
      - `NotebookCreationsHub` được tái thiết kế thành controlled component thuần túy nhận props và callbacks từ trang cha, ngăn chặn lỗi unmount mất trạng thái.
      - Cập nhật checker `isViewingQuiz` trong `AppLayout.tsx` chuyển sang đọc từ query parameter `artifact` đồng bộ.
  - `npm run build` ✅ Hoàn tất biên dịch sạch lỗi 100%.

- **Sprint 16.6 — Centralized Settings & LLMOps Observability Hardening — hoàn thành:**
  - **Phase 1 — Tập trung hoá cấu hình (Centralized Settings):**
    - Thêm 22+ trường `Settings` vào `backend/app/core/config.py` (Pydantic Settings): chunking params, retry/backoff Tenacity, quota limits, batch sizes, RAG search params, Langfuse config, Cloudmersive config — **tất cả có default values**, không còn magic number nào hardcode trong service layer.
    - Loại bỏ toàn bộ `getattr(settings, ...)` fallback trong services; các service `ingestion_service.py`, `retrieval_service.py`, `notebook_chat_service.py`, `quiz_service.py`, `artifact_service.py`, `conversion_service.py` trỏ trực tiếp vào `settings.*`.
    - Làm sạch `backend/.env.example` theo chuẩn tinh gọn: chỉ giữ biến **phải** ghi đè theo môi trường (DB, MinIO, JWT, API Keys, Model Names). Tất cả hằng số thuật toán (retry backoff, batch sizes, chunk sizes…) nằm hoàn toàn trong `config.py`.
  - **Phase 2 — Langfuse LLMOps Metadata Enrichment:**
    - Nâng cấp `backend/app/core/observability.py`: Tự động inject metadata mặc định `chat_model`, `embedding_model`, `environment` ("development"/"production") vào **mọi** trace context.
    - Bọc root trace `@observe_llm(name="document_ingestion")` cho `ingest_asset` trong `ingestion_service.py`; bọc generation span `@observe_llm(name="generate_embeddings_batch", as_type="generation")` cho `_embed_batch_with_retry`.
    - Bọc generation span `@observe_llm(name="generate_query_embedding", as_type="generation")` trong `retrieval_service.py`.
    - Gắn trace context `user_id`, `notebook_id` trong `generate_quiz_mock` (`artifact_service.py`).
  - **Phase 3 — Script Seed Data & CLI Tracing:**
    - Refactor `backend/scripts/seed_data.py`: Đồng bộ `SEED_ADMIN_EMAIL/PASSWORD/FULL_NAME` với `settings.ADMIN_*`; thay `time.sleep(1.0)` hardcode bằng `settings.GEMINI_RETRIEVAL_EMBED_RETRY_MIN_WAIT`.
    - Tạo file proxy `backend/app/seed_data.py` để chạy được cả `python -m app.seed_data`.
    - Thêm `flush_langfuse()` vào khối `finally` của `run_seed()` để đảm bảo tất cả trace được đẩy lên Langfuse Cloud trước khi tiến trình CLI kết thúc.
  - **Langfuse v4 SDK Compatibility Fix:**
    - Cập nhật import trong `observability.py` hỗ trợ đồng thời Langfuse v4+ (`from langfuse import observe, get_client`) và v2/v3 (`from langfuse.decorators import observe, langfuse_context`). Không để lỗi import `langfuse_context` vô hiệu hóa `_IS_LANGFUSE_ENABLED` khi `observe` đã sẵn sàng.
    - Cập nhật `update_current_observation()` sử dụng `client.update_current_generation(...)` (v4 API) và `update_current_span(...)` fallback; `flush_langfuse()` sử dụng `client.flush()` của Langfuse v4.
    - **Verified:** `_IS_LANGFUSE_ENABLED: True`, `observe: <bound method LangfuseDecorator.observe ...>` với `langfuse==4.15.1`.
  - **Test Suite:** `11/11 tests PASSED (100%)` sau toàn bộ các thay đổi.

## Infrastructure

- Docker Compose chạy PostgreSQL `pgvector/pgvector:pg16` và MinIO
- `init-db/01-enable-pgvector.sql` bật extension `vector` khi Postgres khởi tạo volume mới

---

# 5. Next Task

## Ngay lúc này: Sprint 17 — Testing

---

# 6. Technology Stack

## Backend

- FastAPI, SQLAlchemy 2.0, PostgreSQL 16 (JSONB) và pgvector
- MinIO Python SDK
- pwdlib (Argon2id), PyJWT, Pydantic Settings v2
- `python-multipart` cho multipart upload
- `langfuse>=4.x` cho LLM Observability (auto-detect v4 vs v2/v3 import)

## Frontend (implemented)

- React 19 + Vite 8 + TypeScript + Tailwind CSS v3
- React Router v7, Axios, react-hook-form
- TanStack Query v5, react-hot-toast

## AI Stack (chốt từ Sprint 11.5, triển khai dần từ Sprint 12)

- **SDK:** Native SDK Google GenAI (`google-genai`) — gọi thẳng API, **không dùng LangChain** và **không dùng Sentence Transformers**. Lý do: tránh lớp abstraction thừa, dễ kiểm soát prompt/token/chi phí, ít dependency phải bảo trì cho đồ án cá nhân.
- **Embedding model:** `gemini-embedding-001` với `output_dimensionality=768` (Matryoshka Representation Learning) — khớp đúng kiểu cột `VECTOR(768)` trong PostgreSQL.
- **LLM Chat model:** `gemini-3.5-flash-lite` hoặc `gemini-3.1-flash-lite` (chọn theo hạn mức free-tier và độ trễ thực tế) cho chat RAG, intent routing / query condensation và Native Structured Output (response_schema) sinh quiz.
- **Resilience:** Tenacity Retry (exponential backoff) bọc mọi lời gọi embedding/LLM.

## Document Processing

- `libreoffice-writer` (headless) trong Docker image backend: chuyển đổi DOCX → PDF phái sinh ngay khi upload.
- `pypdfium2`: trích xuất text theo từng trang từ PDF — **một pipeline duy nhất** cho cả PDF gốc lẫn DOCX đã convert, nên không cần `python-docx`.

## Database & Search

- PostgreSQL 16 + extension `pgvector` (dense vector) + extension `unaccent` (bỏ dấu tiếng Việt).
- Wrapper `immutable_unaccent(text)` — bọc `unaccent()` thành hàm IMMUTABLE để dùng được trong Generated Column và index.
- Cột `tsv_content` là **Generated Column** (`GENERATED ALWAYS AS (to_tsvector('simple', immutable_unaccent(content))) STORED`) — tsvector không dấu tự sinh, luôn đồng bộ với `content`.
- Index: HNSW (`vector_cosine_ops`) cho vector search và GIN cho full-text search.
- Truy vấn RAG dùng **Hybrid Search RRF** kết hợp Dense (HNSW) + Sparse (GIN).

---

# 7. Current Project Structure

> Cập nhật sau Sprint 16.6. Model `Resource` cũ đã xóa hoàn toàn.

```text
knowledge-sharing-platform/
├── backend/
│   ├── app/
│   │   ├── api/       # health, auth, config, departments, majors, subjects, documents, notebooks (mounted artifacts endpoints)
│   │   ├── core/      # config.py (Pydantic Settings 22+ fields), database.py, security.py, observability.py (Langfuse v4 wrapper)
│   │   ├── models/    # base, enums, user, department, major, subject,
│   │   │              # document, notebook, asset, asset_embedding, notebook_chat, artifact
│   │   ├── schemas/   # auth, department, major, subject, document, asset, notebook, notebook_chat, artifact
│   │   ├── services/  # auth, department, major, subject, document, asset, storage, startup,
│   │   │              # notebook, conversion, ingestion, retrieval, notebook_chat, artifact, quiz
│   │   ├── main.py, seed.py, seed_data.py (proxy cho python -m app.seed_data)
│   ├── scripts/       # seed_data.py (CLI script, dùng settings.ADMIN_*)
│   ├── tests/         # test_chat_sse.py, test_conversion.py, test_ingestion_dedup.py, test_quiz_generation.py
│   ├── alembic/
│   ├── Dockerfile, requirements.txt, .env, .env.example
├── frontend/src/
│   ├── api/           # apiClient, getApiErrorMessage
│   ├── components/ui/ # Button, Input, Modal, Spinner, ErrorMessage, PaginationBar
│   ├── components/    # AdminNavLinks, ProtectedRoute, AdminRoute
│   ├── features/
│   │   ├── auth/      # api, AuthContext, AuthForm
│   │   ├── documents/ # api (Document types), queryKeys (documentsKeys),
│   │   │              # hooks/ (useDocuments, useDocumentDetail, useUploadConfig),
│   │   │              # components/PublicResourceCard, index.ts
│   │   ├── notebooks/ # api, queryKeys, hooks/ (useNotebooks, useCreateNotebook, useNotebookDetail, useNotebookChatStream, useArtifacts...),
│   │   │              # components/ (NotebookCard, CreateNotebookCard, CreateNotebookModal, AddDocumentModal, NotebookChatPanel,
│   │   │              # NotebookCreationsHub, QuizRunner/, GenerateArtifactModal, DeleteArtifactModal...)
│   │   ├── taxonomy/  # api, queryKeys, TaxonomyView, DepartmentMajorSubjectPicker, SubjectSearchInput, hooks/
│   │   └── README.md
│   ├── layouts/       # PublicLayout, AppLayout, AdminLayout
│   ├── pages/         # active: Home, Departments, DepartmentDetail, MajorDetail,
│   │                  #         SubjectDetail, DocumentDetail, Login, Register,
│   │                  #         MyNotebooksPage, NotebookDetailPage,
│   │                  #         MyResources (notice), AdminTaxonomy
│   │                  # stubbed: AdminModeration
│   ├── router/AppRouter.tsx
│   └── utils/parseRouteId.ts
├── init-db/01-enable-pgvector.sql
├── docs/, docker-compose.yml, .env.example
```

---

# 8. Backend Architecture

```text
Client → FastAPI Router → Dependencies/Auth Guard → Service Layer
       → SQLAlchemy Models → PostgreSQL
       → storage_service → MinIO
```

## Frontend Architecture (Sprint 6–8.5)

```text
Browser → React Router → Layouts (Public/App/Admin) + Route Guards
       → TanStack Query + Feature modules (auth, taxonomy, resources)
       → Axios apiClient → FastAPI backend
       → AuthContext/localStorage → JWT session
       → react-hot-toast cho mutation feedback
```

Business logic nằm trong Service Layer; router chỉ bind request/dependency và trả response.

### Document visibility flow (Sprint 8.5+)

- `Document` luôn có `status = PUBLIC` ngay khi tạo qua `seed.py` (nhánh Admin tạm dừng).
- Không có luồng duyệt (`PENDING_REVIEW`) cho đến khi nhánh Admin được mở lại.
- Download file qua presigned URL MinIO (15 phút) thay vì backend proxy — không cần JWT.

### Current API endpoints (Sprint 16.6)

- `GET /health`
- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET /departments/`, `GET /departments/{id}`; admin: `POST`, `PUT`, `DELETE`
- `GET /majors/?department_id=`, `GET /majors/{id}`; admin: `POST`, `PUT`, `DELETE`
- `GET /subjects/?major_id=&q=&limit=`, `GET /subjects/{id}`; admin: `POST`, `PUT`, `DELETE`
- `GET /documents/?subject_id=&resource_type=&page=&size=` (only PUBLIC)
- `GET /documents/{id}` (only PUBLIC, nested assets)
- `GET /documents/{id}/assets/{asset_id}/download` → presigned MinIO URL (no JWT)
- `GET /config/upload`
- `POST /notebooks/` (JWT protected)
- `GET /notebooks/me` (JWT protected)
- `GET /notebooks/{notebook_id}` (JWT protected)
- `PATCH /notebooks/{notebook_id}` (JWT protected)
- `DELETE /notebooks/{notebook_id}` (JWT protected)
- `POST /notebooks/{notebook_id}/saved-documents` (JWT protected)
- `DELETE /notebooks/{notebook_id}/saved-documents/{document_id}` (JWT protected)
- `POST /notebooks/{notebook_id}/assets` (JWT protected)
- `DELETE /notebooks/{notebook_id}/assets/{asset_id}` (JWT protected)
- `GET /notebooks/{notebook_id}/assets/{asset_id}/download` (JWT protected)
- `GET /notebooks/{notebook_id}/assets/{asset_id}/status` (JWT protected)
- `POST /notebooks/{notebook_id}/sessions` (JWT protected)
- `GET /notebooks/{notebook_id}/sessions` (JWT protected)
- `PATCH /notebooks/{notebook_id}/sessions/{session_id}` (JWT protected)
- `DELETE /notebooks/{notebook_id}/sessions/{session_id}` (JWT protected)
- `GET /notebooks/{notebook_id}/sessions/{session_id}/messages` (JWT protected)
- `POST /notebooks/{notebook_id}/sessions/{session_id}/chat` (JWT protected, SSE stream)
- `POST /notebooks/{notebook_id}/artifacts/generate` (JWT protected)
- `GET /notebooks/{notebook_id}/artifacts` (JWT protected)
- `GET /notebooks/{notebook_id}/artifacts/{artifact_id}` (JWT protected)
- `DELETE /notebooks/{notebook_id}/artifacts/{artifact_id}` (JWT protected)

### Frontend routes (Sprint 16)

- Public (active): `/`, `/login`, `/register`, `/departments`, `/departments/:id`, `/majors/:id`, `/subjects/:id`, `/documents/:id`
- Protected (active): `/me/workspace` (MyNotebooksPage), `/me/workspace/:notebookId` (NotebookDetailPage), `/me/resources` (temp notice)
- Admin (active): `/admin/taxonomy`
- Commented out: `/admin/moderation`

---

# 9. Coding Principles

- Service Layer Architecture; Separation of Concerns; Clean Code; Single Responsibility Principle.
- Không query database, đặt business logic hoặc SQL trực tiếp trong Router.
- Không hardcode config; upload limits và MinIO configuration lấy từ `Settings`/environment.
- Frontend: feature modules (`features/{auth,taxonomy,resources}`) + pages lắp ráp; TanStack Query cho server state; query key factory cho cache invalidation.

---

# 10. Technology Decisions

## Nền tảng hiện có

- ORM: SQLAlchemy 2.0, không dùng SQLModel.
- Database: PostgreSQL 16; metadata tài liệu dùng JSONB.
- Storage: MinIO; upload qua backend proxy, download qua presigned URL (15 phút).
- Dual MinIO Client: Tách biệt client gọi nội bộ Docker (MINIO_ENDPOINT=minio:9000) để upload/download ngầm và client ký Presigned URL (MINIO_PUBLIC_ENDPOINT=localhost:9000) để chữ ký HMAC khớp với Host của trình duyệt bên ngoài.
- Migration runtime dùng `Base.metadata.create_all()` xuyên suốt dự án; Alembic scaffold có mặt trong repo nhưng không được sử dụng, quyết định hoãn vô thời hạn (xác nhận lại ở Sprint 15/16).
- Primary key: integer.
- API chưa versioned (`/api/v1` chưa có).
- JWT là single access token HS256, expiry mặc định 24 giờ; chưa có refresh token.
- Centralized configurations: upload limits quản lý tập trung ở settings backend, cấp cho frontend qua `GET /config/upload` (single source of truth).
- Action-Based Hooks Pattern: data fetching và mutation đóng gói thành custom hooks ở feature layer; pages chỉ lắp ghép giao diện.

## Quyết định AI / RAG

- **Native SDK thay vì framework:** dùng `google-genai` trực tiếp, loại bỏ hoàn toàn LangChain và Sentence Transformers — giảm dependency, kiểm soát được prompt và chi phí token, không phải chạy model embedding local (không có GPU).
- **Embedding 768 chiều:** `gemini-embedding-001` hỗ trợ MRL nên cắt xuống `output_dimensionality=768` mà vẫn giữ chất lượng — vừa khớp `VECTOR(768)`, vừa giảm dung lượng index HNSW và chi phí lưu trữ so với chiều mặc định.
- **Model chat rẻ trước, mạnh sau:** mặc định `gemini-3.5-flash-lite` / `gemini-3.1-flash-lite` cho cả routing lẫn trả lời; chỉ cân nhắc model lớn hơn nếu chất lượng thực đo không đạt.
- **Hybrid Search RRF thay vì chỉ vector search:** tiếng Việt nhiều thuật ngữ/mã môn học và viết tắt mà vector thuần dễ trượt; kết hợp Dense (HNSW cosine) + Sparse (GIN full-text) rồi hợp nhất bằng Reciprocal Rank Fusion để ổn định thứ hạng mà không cần tinh chỉnh trọng số theo từng truy vấn.
- **Không dấu ở tầng database:** `unaccent` + wrapper `immutable_unaccent` + Generated Column `tsv_content` đảm bảo người dùng gõ có dấu hay không dấu đều khớp, và không cần code Python đồng bộ lại tsvector mỗi lần ghi.
- **Convert DOCX → PDF thay vì parse DOCX riêng:** LibreOffice headless sinh PDF phái sinh dùng chung cho cả preview trên UI và trích xuất text bằng `pypdfium2` — một định dạng đầu vào duy nhất cho pipeline AI, đồng thời số trang trong citation khớp đúng với bản người dùng đang xem.
- **Page-aware chunking:** cắt chunk trong phạm vi từng trang, **không overlap xuyên trang**; `page_number` lưu ở cột riêng chứ không nhúng vào nội dung đem đi embedding. Đổi lại một chút ngữ cảnh ở ranh giới trang để citation click-to-jump luôn nhảy đúng trang.
- **Embed một lần cho mỗi Asset:** vector gắn theo `asset_id`, nên một Document công khai được nhiều Notebook lưu chỉ tốn chi phí embedding một lần.
- **Xử lý nền, không chặn request:** convert và ingest chạy qua FastAPI `BackgroundTasks` với `db_session` độc lập; trạng thái theo dõi bằng `ingestion_status` (PENDING/PROCESSING/COMPLETED/FAILED) và frontend polling.
- **Local-First & Cloud-Ready:** toàn bộ hạ tầng chạy local bằng Docker Compose (PostgreSQL + pgvector, MinIO), nhưng mọi endpoint/credential đều đọc từ `.env` — đổi sang cloud (Vercel cho FE, Render cho BE, Supabase cho Postgres, Cloudflare R2 cho object storage tương thích S3) chỉ bằng cách đổi biến môi trường, không sửa code.
- **Kiểm thử theo sprint:** mỗi sprint backend (11.5, 12, 13) phải có script test độc lập chạy xanh trước khi mở sprint kế tiếp.

---

# 11. Non-functional Requirements & Constraints

## Upload

- Chỉ nhận PDF và DOCX được xác thực nội dung cơ bản, không chỉ dựa extension.
- Giới hạn mặc định 30 MB/file và 5 asset/resource, có thể cấu hình bằng environment.
- Chưa có virus scan, download endpoint hay presigned URL trong code hiện tại.

## Known Risks / Constraints

- Đồ án solo trong một học kỳ; ngân sách API Gemini và GPU free-tier hạn chế.
- AI Pipeline/RAG chưa triển khai, nên không mô tả như tính năng đã có.

---

# 12. Roadmap

1. ✅ Backend Foundation
2. ✅ Authentication
3. ✅ Department + Major + Subject
4. ✅ Resource (DB Refactor & CRUD)
5. ✅ Upload System & Visibility Workflow
6. ✅ FE Foundation
7. ✅ FE Catch-up Features
8. ✅ Code Structure Refactor
8.5. ✅ **Database Architecture Refactor** — **hoàn thành**
9. ✅ **UI/UX Polish & Design Consistency** — **hoàn thành**
10. ✅ **Notebook (AI Workspace) Feature — Dashboard + Layout Redesign** — **hoàn thành**
10.5. ✅ **Notebook Dashboard Actions (Rename/Delete)** — **hoàn thành**
11. ✅ **Notebook Detail Page & Document Saving / Asset Upload** — **hoàn thành**
11.5. ✅ **Document Conversion & Preview Debt Cleanup** — **hoàn thành** — chuyển đổi DOCX → PDF bằng LibreOffice headless, `converted_pdf_path`, mở khóa preview DOCX
12. ✅ **Ingestion Pipeline (Backend only)** — **hoàn thành**
13. ✅ **Retrieval Engine & Chat API (Backend only)** — **hoàn thành** — Hybrid Search RRF (Dense + Sparse), Intent Routing/Condensation qua `gemini-3.5-flash-lite`, SSE streaming chat API kèm trích dẫn trang
14. ✅ **Chat Frontend & Citation UI** — **hoàn thành** — giao diện chat ở cột phải `NotebookDetailPage`, streaming câu trả lời, `CitationBadge` click nhảy thẳng trang PDF (`#page=X`)
15. ✅ **Quiz Studio (Backend)** — **hoàn thành** — thiết kế model NotebookArtifact, Multi-Asset Linear Space Sampling (Linspace), Bloom instruction, Google GenAI SDK sinh JSON trích xuất từ `selected_asset_ids`
16. ✅ **Quiz Studio (Frontend)** — **hoàn thành** — api.ts, queryKeys, useArtifacts hooks, creations panel/modal, Quiz Runner interactive interface
16.5. ✅ **Tối ưu hóa Tầng Service, LLM Observability & Hoàn thiện Trải nghiệm (Hardening)** — **hoàn thành** — SHA-256 deduplication, Streaming PDF memory optimization (<30MB RAM), SSE token tracking, Dual-Mode Cloudmersive conversion, Langfuse Cloud tracing, Soft Pastel EdTech theme, Google OAuth 2.0
16.6. ✅ **Centralized Settings & LLMOps Observability Hardening** — **hoàn thành** — 22+ Pydantic Settings fields thay thế toàn bộ magic numbers; Langfuse v4.x SDK compatibility; `@observe_llm` cho document_ingestion, embeddings batch, query_embedding; seed_data CLI flush; `.env.example` tinh gọn
17. 🔄 **Testing** — **đang triển khai** — unit/integration test backend, test luồng chính frontend, hoàn thiện seed/fixture cho demo
18. ⏳ **Deployment & Optimization** — **kế hoạch** — Docker hóa production, chuyển Cloud (Vercel/Render/Supabase/R2) qua `.env`, tối ưu chi phí token

> **Lý do tách sprint AI/RAG:** mỗi sprint từ 11.5 đến 18 phải tự kiểm thử độc lập (backend có script test riêng chạy xanh) trước khi bắt đầu sprint kế tiếp — đúng pattern đã áp dụng ở Sprint 11. Việc này tránh gom nhiều tầng vào một sprint gây quá tải, khó debug và khó rollback từng phần.

---

# 13. AI Architecture

## Pipeline tổng thể

```text
Upload (PDF/DOCX)
  → [Sprint 11.5] LibreOffice headless: DOCX → PDF phái sinh (converted_pdf_path, MinIO)
  → [Sprint 12] pypdfium2: trích xuất text theo từng trang
  → [Sprint 12] Page-aware chunking (không overlap xuyên trang)
  → [Sprint 12] google-genai: gemini-embedding-001 (768d) → AssetEmbedding (pgvector)
  → [Sprint 13] Hybrid Search RRF: Dense HNSW + Sparse GIN
  → [Sprint 13] gemini-3.5-flash-lite: intent routing / condensation + trả lời kèm citation (SSE streaming)
  → [Sprint 14] Chat UI + CitationBadge (#page=X)
  → [Sprint 15] Native Structured Output: sinh trắc nghiệm (NotebookArtifact QUIZ)
```

## Tầng lưu trữ vector

Bảng `AssetEmbedding` gắn theo `asset_id` (không phải `notebook_id`) vì `Asset` đã là tầng file dùng chung — xem mục 19c:

- `id`, `asset_id` (FK CASCADE), `chunk_index`, `content`, `page_number`, `metadata` JSONB, `created_at`
- `embedding VECTOR(768)` — khớp `output_dimensionality=768` (MRL) của `gemini-embedding-001`
- `tsv_content` — Generated Column: `GENERATED ALWAYS AS (to_tsvector('simple', immutable_unaccent(content))) STORED`
- Index: HNSW `vector_cosine_ops` trên `embedding`, GIN trên `tsv_content`
- Extension bắt buộc: `vector`, `unaccent` + wrapper `immutable_unaccent(text)` (IMMUTABLE để dùng được trong generated column/index)

Bảng `assets` bổ sung: `converted_pdf_path` (Sprint 11.5), `file_hash`, `ingestion_status` (PENDING/PROCESSING/COMPLETED/FAILED), `ingestion_error`, `chunk_count` (Sprint 12).

## Chuẩn hóa & trích xuất

- DOCX luôn được convert sang PDF trước, nên pipeline AI chỉ phải xử lý **một định dạng duy nhất**; file gốc vẫn giữ nguyên cho nút "Tải về".
- `pypdfium2` đọc text theo từng trang, giữ được `page_number` thật khớp với bản PDF người dùng xem trên UI.
- Guard tài liệu scan: tổng số ký tự trích xuất < 100 → đánh dấu `FAILED` với mã `SCANNED_DOCUMENT_UNSUPPORTED` (chưa làm OCR trong phạm vi đồ án).

## Chunking

- **Page-aware:** duyệt từng trang độc lập, chunk không bao giờ vắt qua ranh giới trang.
- Kích thước 500–700 tokens (~1500–2000 ký tự), overlap 100 tokens **trong phạm vi cùng một trang**.
- `page_number` lưu ở cột riêng, không chèn vào nội dung đem đi embedding để tránh nhiễu vector.
- Mục tiêu: citation trả về luôn nhảy đúng trang PDF (`#page=X`) 100%, không lệch trang.

## Truy hồi (Retrieval) — Hybrid Search RRF

- **Dense:** cosine similarity trên HNSW index của `embedding` — bắt được câu hỏi diễn đạt tự do, khác từ ngữ với tài liệu.
- **Sparse:** full-text search trên GIN index của `tsv_content` (tsvector không dấu) — bắt chính xác thuật ngữ, mã môn học, tên riêng, và không phụ thuộc người dùng gõ dấu.
- **RRF (Reciprocal Rank Fusion):** hợp nhất hai bảng xếp hạng theo thứ hạng thay vì theo điểm số, nên không cần chuẩn hóa/tinh chỉnh trọng số giữa hai hệ đo khác nhau.
- Phạm vi truy vấn của một Notebook gồm 2 nguồn: (a) Asset thuộc chính Notebook, (b) Asset của Document đã lưu qua `Notebook_Saved_Documents`.

## Sinh câu trả lời

- Intent routing / query condensation bằng `gemini-3.1-flash-lite` để rút gọn câu hỏi theo lịch sử hội thoại trước khi truy hồi.
- Trả lời dạng SSE streaming, kèm trích dẫn nguồn (tên tài liệu + số trang) để frontend render `CitationBadge`.
- Quiz và flashcards dùng Native Structured Output trên tập `selected_asset_ids` do người dùng chọn (Sprint 15).

## Đặc tả kỹ thuật Sprint 13 — Retrieval Engine & Chat API (Backend only)

### 1. Database models & Citation Shapes

- **`NotebookChatSession`:** `id`, `notebook_id` (FK CASCADE), `user_id` (FK CASCADE), `title` (mặc định `"Phiên trò chuyện mới"`), `created_at`, `updated_at`.
- **`NotebookChatMessage`:** `id`, `session_id` (FK CASCADE), `role` (`user` / `assistant`), `content`, `citations` JSONB, `created_at`.
- **Cascade: ** Xóa Notebook → xóa session → xóa message tự động (CASCADE).
- **Trích dẫn Pruned Citation:** Trường `citations` lưu trong DB và trả về cho FE là dạng mảng đối tượng JSONB đã được tỉa (prune) sạch nội dung text thô để tối ưu lưu trữ. Cấu trúc JSON nhận diện ở FE:
  ```json
  [
    {
      "index": 1,
      "file_name": "filename.pdf",
      "page_number": 3,
      "asset_id": 45
    }
  ]
  ```
  *(Lưu ý: Không có trường `content` trong DB record này. FE dựa vào `file_name` và `page_number` để hiển thị CitationBadge và click để Preview PDF cuộn đến trang tương ứng).*

### 2. Chat API Endpoints Registry

Mọi tương tác từ Client (Frontend) sử dụng các endpoint sau (đều yêu cầu Header `Authorization: Bearer <JWT>`):

| HTTP Method | URL Path | Mô tả | Trả về (200 OK / 201 Created) |
| :--- | :--- | :--- | :--- |
| **POST** | `/notebooks/{notebook_id}/sessions` | Tạo một phiên chat mới | Đối tượng Session JSON |
| **GET** | `/notebooks/{notebook_id}/sessions` | Lọc toàn bộ phiên chat của notebook | Mảng các Sessions |
| **PATCH** | `/notebooks/{notebook_id}/sessions/{session_id}` | Đổi tên tiêu đề phiên chat | Đối tượng Session đã sửa |
| **DELETE** | `/notebooks/{notebook_id}/sessions/{session_id}` | Xóa vĩnh viễn phiên chat (Cascade) | `{"status": "deleted"}` |
| **GET** | `/notebooks/{notebook_id}/sessions/{session_id}/messages` | Lấy toàn bộ lịch sử trò chuyện (sắp xếp tăng dần thời gian) | Mảng các Messages (có `citations`) |
| **POST** | `/notebooks/{notebook_id}/sessions/{session_id}/chat` | Nhận câu hỏi, RAG truy hồi, định tuyến và stream kết quả về | **Server-Sent Events (SSE) Stream** |

> [!WARNING]
> **Legacy Restriction:** Endpoint `POST /notebooks/{notebook_id}/sessions/{session_id}/messages` cũ ghi đè tin nhắn trực tiếp **đã bị khóa cứng bằng HTTP 403 Forbidden** đối với người dùng thông thường để bắt buộc mọi hội thoại phải đi qua luồng tạo và stream SSE của endpoint `/chat`.

### 3. Quy ước Server-Sent Events (SSE) Protocol

Khi kết nối vào endpoint `/chat`, server trả dữ liệu stream dưới định dạng `text/event-stream`. Có 4 tên sự kiện (`event`) bắt buộc bắn về theo thứ tự quy chuẩn:

1. **`event: citations`**
   - *Thời điểm:* Bắn ngay tức thì sau khi hoàn thành truy hồi Hybrid Search (trước khi LLM bắt đầu sinh câu trả lời).
   - *Payload:* Mảng đối tượng trích dẫn được chọn cho ngữ cảnh (đã được cắt bớt `content` để tiết kiệm băng thông):
     ```text
     data: [{"index": 1, "file_name": "tailieu.pdf", "page_number": 2, "asset_id": 10}]
     ```
2. **`event: delta`**
   - *Thời điểm:* Bắn liên tục cho từng cụm token được sinh ra từ Google Gemini.
   - *Payload:* Chuỗi text thô bọc trong nháy kép JSON:
     ```text
     data: "FastAPI "
     ```
3. **`event: done`**
   - *Thời điểm:* Khi hoàn thành stream thành công và tin nhắn đã được transaction commit vào cơ sở dữ liệu.
   - *Payload:* Chứa định danh `session_id`, `message_id` tin nhắn trợ lý vừa lưu, và câu hỏi rút gọn (`condensed_query`):
     ```text
     data: {"session_id": 1, "message_id": 105, "condensed_query": "What is FastAPI?"}
     ```
4. **`event: error`**
   - *Trường hợp thất bại:* Xảy ra lỗi LLM, lỗi DB giữa chừng. Client hiển thị lỗi trên UI và tự ngắt kết nối.
     ```text
     data: {"detail": "Error message content"}
     ```

### 4. Quyết định kỹ thuật & Registry cấu hình

* **GEMINI_CHAT_MODEL:** `gemini-3.1-flash-lite` (Xác nhận hoạt động an toàn và phản hồi nhanh trong môi trường phát triển).
* **GEMINI_EMBEDDING_MODEL:** `gemini-embedding-001` (Kích thước output cắt xuống 768 chiều).
* **HNSW Index Params:** pgvector index cosine: `m=16`, `ef_construction=64`.
* **Hybrid Search RRF Formula:**
  - Lấy Top-20 Dense (bằng cosine distance) + Top-20 Sparse (bằng GIN `ts_rank_cd` không dấu).
  - Điểm RRF: $Score = \sum \frac{1}{60 + Rank_{\text{dense}}} + \sum \frac{1}{60 + Rank_{\text{sparse}}}$.
  - Lấy Top-5 chunks có điểm RRF cao nhất để nạp vào prompt context.
* **Token Budget Control:** Khống chế nội dung context tối đa 3000 tokens (đếm thực tế bằng Gemini `count_tokens` API). Nếu vượt quá, loại bỏ các chunk điểm RRF thấp nhất.
* **Chat Context Size:** Sử dụng Sliding Window 6 tin nhắn gần nhất để condense query, bỏ qua LLM (Fast-path bypass) nếu là tin nhắn đầu tiên.
* **Concurrency Guard:** Lock ghi in-memory (`asyncio.Lock` chia theo `session_id`) để chặn việc gọi song song 2 request chat trên cùng một phiên (lỗi `409 Conflict`).
* **Atomic write-on-complete:** Chỉ ghi tin nhắn vào DB sau khi stream thành công. Cho phép rollback/hủy bỏ khi phát hiện disconnect (`request.is_disconnected()`).

---

## Đặc tả kỹ thuật Sprint 14 — Chat Frontend & Citation UI

- **`useNotebookChatStream`:** hook quản lý kết nối SSE qua `ReadableStream`, parse từng event (`citations` / `delta` / `done` / `error`), tích lũy nội dung để render dần; tích hợp `AbortController` cho nút "Dừng tạo" và tự hủy khi unmount.
- **`NotebookChatPanel.tsx`:** cột chat hoàn chỉnh trong `NotebookDetailPage` — danh sách message (user/assistant), auto-scroll, ô input đổi nút **Gửi ⇄ Dừng** theo cờ `isStreaming`, chặn gửi khi đang stream.
- **`ChatSessionHistoryPopover.tsx`:** popover lịch sử chat — tìm kiếm theo tiêu đề session, rename / delete, tái dùng hook `useClickOutside` đã có từ Sprint 11.
- **`CitationBadge.tsx`:** parse tag `[X]` trong markdown câu trả lời; nếu `X` khớp một mục trong metadata `citations` thì render badge bấm được, mở `PdfPreviewModal` nhảy đúng `#page=X`; nếu LLM **bịa số** không khớp thì render như text thường (không tạo link chết).
- **Render nội dung:** tích hợp **KaTeX** cho công thức toán và nút copy cho code block.
- Sprint 14 không đổi backend: mọi hành vi chat đã được Sprint 13 chốt và test độc lập.

## Đặc tả kỹ thuật Sprint 15 — Quiz Studio (Backend)

Sprint 15 tập trung phát triển phần Core logic và API cho tính năng sinh câu hỏi trắc nghiệm (Quiz) từ tài liệu trong Sổ tay:

### 1. Cơ sở dữ liệu & Model
- **Model `NotebookArtifact`**: Bảng dữ liệu tự sinh qua `create_all()` khi chạy app, **không dùng Alembic** ở sprint này.
- **Fields**:
  - `id`: integer primary key.
  - `notebook_id`: foreign key liên kết với Notebook (CASCADE).
  - `artifact_type`: enum `ArtifactType` gồm 3 giá trị `QUIZ`, `FLASHCARD`, `SUMMARY` (thực tế code backend chỉ support sinh `QUIZ`).
  - `content`: kiểu dữ liệu JSONB lưu trữ cấu trúc đề quiz.
  - `created_at`, `updated_at`.
- **Computed field**: `total_items` trong schema Pydantic là trường tính toán từ số phần tử của câu hỏi `len(content["questions"])`, **không** lưu thành cột trong Database.

### 2. API Endpoints
Cung cấp 4 API endpoints được bảo vệ bởi JWT (validate ownership và quyền sở hữu Notebook):
- `POST /notebooks/{notebook_id}/artifacts/generate`: Nhận request chứa `selected_asset_ids` (phải thuộc Notebook đó) và `artifact_type` (chỉ nhận `QUIZ`), trả về thông tin artifact vừa được sinh.
- `GET /notebooks/{notebook_id}/artifacts/`: Liệt kê các artifacts của Notebook.
- `GET /notebooks/{notebook_id}/artifacts/{artifact_id}`: Xem chi tiết một artifact.
- `DELETE /notebooks/{notebook_id}/artifacts/{artifact_id}`: Xóa artifact khỏi Notebook.

### 3. Quy trình thực hiện & Validation (Phase 1 & Phase 2)
- **Phase 1: Stub/Mock Generator & Validation**
  - Validation:
    - User sở hữu notebook (`Notebook.owner_id == current_user.id`).
    - Tất cả tài liệu chọn phải thuộc notebook. `Asset` của `selected_asset_ids` phải có `ingestion_status == 'COMPLETED'`.
    - Quota check: Giới hạn `MAX_ARTIFACTS_PER_NOTEBOOK = 20` (nếu vượt quá trả lỗi HTTP 400).
    - Rate limit: Cooldown 15 giây giữa hai lần generate của cùng một user (HTTP 429 nếu vi phạm).
  - Môi trường thử nghiệm: Endpoint generate sẽ trả dữ liệu trắc nghiệm giả lập (mock/stub) để kiểm thử đầy đủ các nhánh lỗi và logic nghiệp vụ mà không tốn quota/chi phí AI thực tế.
  - **Multi-Asset Linear Space Sampling (Numpy-style Linspace)**:
    - Ngân sách chunk tối đa là 30 chunks chia đều cho số lượng tài liệu (`selected_asset_ids`) được chọn: `budget_per_asset = max(1, 30 // len(selected_asset_ids))`.
    - Đối với mỗi tài liệu, nếu số chunk thực tế nhỏ hơn hoặc bằng ngân sách được phân bổ (`total_chunks <= budget_per_asset`) thì lấy toàn bộ (không sampling).
    - Ngược lại, áp dụng thuật toán nội suy khoảng cách đều (Numpy-style Linspace Sampling) theo công thức:
      $$\text{index}_i = \text{round}\left( \frac{i \times (\text{total\_chunks} - 1)}{\text{budget\_per\_asset} - 1} \right) \quad \text{với } i \in [0, \text{budget\_per\_asset} - 1]$$
    - **Ưu điểm kỹ thuật cốt lõi**:
      * **Bao phủ 100% biên tài liệu:** Luôn lấy trọn vẹn cả chunk mở đầu (`index = 0` tại $i = 0$) và chunk kết luận cuối cùng (`index = \text{total\_chunks} - 1` tại $i = \text{budget\_per\_asset} - 1$).
      * **Triệt tiêu hiện tượng Undershoot:** Khắc phục triệt để nhược điểm của phương pháp bước nhảy nguyên `step = N // K` (thường bị dồn cục ở đầu tài liệu và bỏ sót hoàn toàn các trang kết luận/tóm tắt ở cuối tài liệu).
  - **Prompting & Bloom's Taxonomy Guide**:
    - Sử dụng `system_instruction` có cấu trúc cố định thiết lập câu hỏi: khoảng 30% câu hỏi ở mức Nhận biết (khái niệm, định nghĩa cơ bản) và 70% câu hỏi ở mức Thông hiểu/Suy luận.
    - Metodo: **Không** sử dụng trường `difficulty` (độ khó) trong request, schema hay API/UI.
  - **Gemini Integration**:
    - Gọi model `gemini-3.1-flash-lite` thông qua Google GenAI SDK. Tái sử dụng client và decorator tenacity retry đã cài đặt sẵn ở Sprint 12-13.
    - Cấu hình Native Structured Output định nghĩa schema JSON trả về (questions, options, correct_answer, explanation) để đảm bảo kết quả sinh ra khớp cấu trúc lưu trữ và không cần parse thủ công.
  - **Test Suite**: Bộ test độc lập `test_quiz_generation.py` chạy độc lập kiểm thử chất lượng sinh và các logic biên.

---

## Đặc tả kỹ thuật Sprint 16 — Quiz Studio (Frontend)

Sprint 16 tích hợp hoàn chỉnh giao diện chơi trắc nghiệm và quản lý các sản phẩm học tập AI Artifacts:

### 1. Data Layer & Hooks
- File `frontend/src/features/notebooks/api.ts` bổ sung các API call tương tác với endpoint artifact.
- Định nghĩa schema `queryKeys` quản lý dữ liệu cache.
- Triển khai 4 custom hooks quản lý server-state: `useArtifacts`, `useArtifactDetail`, `useGenerateQuiz`, `useDeleteArtifact`.

### 2. UI Components
- **`NotebookCreationsHub.tsx`**: Bảng điều khiển quản lý các sản phẩm sáng tạo AI trực thuộc Sổ tay (Artifacts Hub), làm nơi hiển thị danh sách các bài Quiz đã được lưu để người dùng ôn tập / thi thử lại.
- **`ArtifactCard.tsx`**: Thẻ hiển thị tóm tắt thông tin một artifact (loại hình, số câu hỏi `total_items`, thời gian tạo).
- **`GenerateArtifactModal.tsx`**: Modal cấu hình thiết lập tạo bài ôn tập. Cho phép lựa chọn danh sách tệp nguồn đã qua xử lý (`ingestion_status == COMPLETED`) và lựa chọn số lượng câu hỏi ôn tập (5, 10, 15, hoặc 20 câu).
  - Cảnh báo: Các tài liệu có trạng thái `ingestion_status != COMPLETED` sẽ bị disable/dim checkbox đi kèm badge biểu thị trạng thái (PROCESSING/FAILED) tương ứng để người dùng biết.
- **`DeleteArtifactModal.tsx`**: Modal cảnh báo xác nhận trước khi thực hiện xóa vĩnh viễn bài tập trắc nghiệm khỏi Sổ tay, đồng bộ hóa cache TanStack Query sau khi kết thúc.
- **`QuizRunner.tsx`**: Trình chơi trắc nghiệm:
  - `QuizHeader`: Tiêu đề, số câu trả lời đúng/tổng, nút Reset làm lại.
  - `QuizQuestionItem`: Hiển thị nội dung câu hỏi, danh sách radio button chọn đáp án, và cung cấp phản hồi lập tức (instant feedback) khi người dùng chọn (màu xanh nếu đúng, màu đỏ nếu sai và hiện lời giải giải thích chi tiết).

### 3. Kiến trúc State & URL Synchronization
- **Lập trạng thái Page-level (`activeArtifactId`)**: Trạng thái active của bài trắc nghiệm được quản lý tại trang cha `NotebookDetailPage.tsx` nhờ hook `useSearchParams` từ query URL `?artifact={id}`.
- **Lý do thiết kế**: Vì `NotebookCreationsHub` và `QuizRunner` là hai layout con hiển thị loại trừ lẫn nhau (CreationsHub bị unmount khi chơi quiz để QuizRunner chiếm trọn khu vực làm việc). Việc đưa state lên trang cha và đồng bộ với URL giúp ngăn chặn việc mất trạng thái khi unmount, đồng thời hỗ trợ nút điều hướng Back/Forward và click-to-share link một cách tự nhiên.
- **Controlled Component**: `NotebookCreationsHub` được triển khai dưới dạng controlled component thuần túy nhận prop `onSelectArtifact` từ `NotebookDetailPage.tsx` để điều hướng qua SearchParams mà không tự giữ trạng thái local.
- **URL parameter sync in AppLayout**: Cập nhật hàm `isViewingQuiz` trong `AppLayout.tsx` chuyển trạng thái kiểm tra từ `quizId` sang `artifact` để thống nhất cấu trúc router.

---

## Đặc tả kỹ thuật Sprint 16.5 — Tối ưu hóa Tầng Service, LLM Observability & Hoàn thiện Trải nghiệm (Hardening)

### 1. Mục tiêu & Bối cảnh Kỹ thuật
Sau khi hoàn thành tạo bài tập Quiz và Hub sáng tạo ở Sprint 16, Sprint 16.5 tập trung gia cố độ ổn định toàn diện (System Hardening), tối ưu hóa hiệu năng tài nguyên (RAM/CPU/Token), tích hợp hệ thống giám sát LLM thời gian thực và đồng bộ trải nghiệm người dùng trước khi bước vào Sprint 17 (Đánh giá Thực nghiệm Ragas) và Sprint 18 (Đóng gói Docker & Triển khai).

---

### 2. Các Hạng mục Kỹ thuật đã Triển khai

#### A. Tầng Backend & Core AI Pipeline
* **Ingestion Pipeline & Content-addressable Deduplication (`ingestion_service.py`):**
  * Tích hợp cơ chế kiểm tra trùng lặp qua mã băm SHA-256 (`file_hash`). Tái sử dụng toàn bộ vector embedding từ các Asset đã `COMPLETED` cùng hash (tự sinh ID mới), bỏ qua hoàn toàn việc gọi Gemini Embedding API (tiết kiệm 100% chi phí AI và thời gian chờ).
  * Chuyển đổi cơ chế đọc PDF sang **Streaming Page-by-page Generator (`pypdfium2`)** với khối `try...finally` đóng tài nguyên C-layer (`page.close()`, `textpage.close()`) ngay sau mỗi trang, duy trì bộ nhớ RAM phẳng ($< 30\text{MB}$).
* **Token Tracking & SSE Stream (`notebook_chat_service.py`):**
  * Trích xuất `usage_metadata` (`prompt_token_count`, `candidates_token_count`) từ luồng stream của Google GenAI SDK.
  * Lưu trữ chính xác vào cơ sở dữ liệu (`NotebookChatMessage`) và trả về chi tiết (`prompt_tokens`, `completion_tokens`, `total_tokens`) trong sự kiện `event: done`.
* **Dual-Mode Document Conversion Engine (`conversion_service.py`):**
  * Thiết kế kiến trúc **Dual-Mode Adapter**: Ưu tiên sử dụng **Cloudmersive REST API** (`POST /convert/docx/to/pdf`) khi có API Key để giải phóng 100% RAM/CPU của server Backend khi deploy Cloud; tự động fallback sang subprocess `soffice` (LibreOffice) khi chạy offline trên máy dev.
  * Đồng bộ cơ chế bắt lỗi: Cập nhật dứt khoát `conversion_status = FAILED`, `ingestion_status = FAILED` (`CONVERSION_FAILED`) khi cả 2 phương thức đều không thành công.
* **LLM Observability với Langfuse Cloud (`observability.py` & `config.py`):**
  * Tích hợp SDK `langfuse>=2.0.0` với module wrapper an toàn (`@observe_llm`, `update_trace_context`), tự động chuyển sang chế độ no-op trong suốt khi chạy offline test mà không cần kết nối mạng.
  * Giám sát toàn diện luồng RAG Chat (`notebook_rag_chat_stream`), rút gọn ngữ cảnh (`condense_query`) và sinh bài tập (`generate_quiz`).
* **Nâng cấp Hệ thống Prompt & Phân tích Đánh giá (Pedagogical Standards):**
  * **RAG Chat:** Định hình Persona Trợ giảng thông thái ("tôi" - "bạn"), trả lời trực diện và phân tích sâu, chuẩn hóa trích dẫn số `[1]`, `[2]` gắn liền sau luận điểm, loại bỏ các câu mở đầu rập khuôn máy móc.
  * **Quiz Generation:** Chuẩn hóa theo Bloom Taxonomy (30% Nhận biết/Hiểu, 70% Vận dụng/Suy luận logic). Thiết lập cấu trúc lời giải thích 3 tầng (Self-contained Reasoning: *Bản chất lý thuyết* $\rightarrow$ *Suy luận/Giải từng bước* $\rightarrow$ *Phân tích loại trừ phương án sai*).
  * **Linspace Sampling Algorithm:** Đồng bộ hóa công thức lấy mẫu chunk khoảng cách đều $\text{index}_i = \text{round}\left( \frac{i \times (N - 1)}{K - 1} \right)$, đảm bảo độ phủ 100% toàn bộ tài liệu (không bỏ sót trang mở đầu và trang kết luận).

#### B. Tầng Giao diện Frontend (UI/UX & Performance)
* **Design System (Soft Pastel EdTech Theme):**
  * Nền ấm dịu mắt `#FAF9F6`, thanh Sidebar đen than `#13141A`, Card bo tròn mềm mại (`rounded-2xl`).
  * Bộ màu Pastel trực quan: Thảo luận (`#F5F0FF`), Quiz (`#E6FFFA`), Flashcard (`#F0FDF4`).
* **Chuyển trang Mượt mà & Tối ưu Hiệu năng:**
  * Tích hợp `framer-motion` (`PageTransition.tsx`) xử lý mượt mà chuyển cảnh giữa các route, khắc phục lỗi mất thanh cuộn.
  * Triển khai Route Lazy Loading (`React.lazy` + `<Suspense>`) và hệ thống Skeleton Loading trên tất cả các trang chính.
* **Xác thực Google OAuth 2.0:**
  * Tích hợp nút đăng nhập Google mượt mà trên Frontend, kết hợp API `POST /auth/google` tự động liên kết tài khoản và gán quyền `STUDENT`.

---

### 3. Kết quả Xác thực (Verification & Test Suite)
* **Automated Backend Tests:** `11/11 tests PASSED (100%)` trên Python 3.12 (bao gồm kiểm thử Deduplication, Streaming Memory, Dual-mode Conversion, SSE Token Tracking, Quiz JSON Schema Validation).
* **Frontend Build & Lint:** `tsc -b && vite build` thành công $100\%$, 0 lỗi TypeScript và ESLint.

---

## Đặc tả kỹ thuật Sprint 16.6 — Centralized Settings & LLMOps Observability Hardening

### 1. Mục tiêu
Loại bỏ toàn bộ "magic numbers" hardcode trong service layer AI, tập trung 100% tham số cấu hình vào `backend/app/core/config.py` (Pydantic Settings), đồng thời hoàn thiện hệ thống LLMOps với Langfuse Cloud.

### 2. Centralized Settings — `config.py` (Nhóm mới thêm)

| Nhóm | Biến tiêu biểu | Default |
|:-----|:---------------|:--------|
| Embedding Batch | `GEMINI_EMBEDDING_MAX_CHUNKS_PER_BATCH` | 80 |
| Embedding Batch | `GEMINI_EMBEDDING_TPM_BUDGET_PER_BATCH` | 24000 |
| Ingestion Chunking | `INGESTION_CHUNK_SIZE_WORDS` | 600 |
| Ingestion Chunking | `INGESTION_CHUNK_OVERLAP_WORDS` | 100 |
| Ingestion Retry | `GEMINI_EMBEDDING_RETRY_ATTEMPTS` | 6 |
| Ingestion Retry | `GEMINI_EMBEDDING_RETRY_MAX_WAIT` | 60.0 |
| RAG Retrieval | `RAG_DENSE_SEARCH_TOP_K`, `RAG_SPARSE_SEARCH_TOP_K` | 20 |
| RAG Retrieval | `RAG_RRF_K`, `RAG_RRF_TOP_K` | 60.0, 5 |
| RAG Retrieval | `RAG_CONTEXT_MAX_TOKENS` | 3000 |
| Chat Condensation | `CHAT_HISTORY_SLIDING_WINDOW_SIZE` | 6 |
| Quiz | `QUIZ_GENERATION_CHUNK_BUDGET` | 30 |
| Observability | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` | — |
| Conversion | `CLOUDMERSIVE_API_KEY`, `CLOUDMERSIVE_TIMEOUT_SECONDS` | — |

**Nguyên tắc `.env.example`:** Chỉ chứa biến **bắt buộc ghi đè** theo môi trường (DB credentials, MinIO, JWT, API Keys, Model Names). Tất cả hằng số thuật toán giữ default trong `config.py`.

### 3. Observability Coverage (`observability.py` — Langfuse v4 Compatible)

- **Import strategy:** Ưu tiên `from langfuse import observe, get_client` (v4+); fallback `from langfuse.decorators import observe, langfuse_context` (v2/v3). Không để lỗi import làm vô hiệu hóa `_IS_LANGFUSE_ENABLED`.
- **Context helpers:**
  - `observe_llm(name=..., as_type=...)` — decorator bọc sync/async/async-gen, auto-inject default metadata.
  - `update_trace_context(**kwargs)` — cập nhật metadata trace (v4: `client.update_current_span()`; v3: `langfuse_context.update_current_trace()`).
  - `update_current_observation(**kwargs)` — cập nhật generation span (v4: `client.update_current_generation(model=..., usage_details=...)`).
  - `flush_langfuse()` — flush safe (v4: `client.flush()`; v3: `langfuse_context.flush()`); no-op khi disabled.
- **Default metadata tự động:** `environment` ("development"/"production"), `chat_model`, `embedding_model` inject vào mọi trace.
- **Traces đã cover:**
  - `document_ingestion` (root span) → `generate_embeddings_batch` (generation span) — `ingestion_service.py`
  - `generate_query_embedding` (generation span) — `retrieval_service.py`
  - `notebook_rag_chat_stream`, `condense_query`, `generate_quiz` — `notebook_chat_service.py`, `artifact_service.py`

### 4. Seed Data CLI (`backend/scripts/seed_data.py`)

- Đồng bộ admin credentials từ `settings.ADMIN_EMAIL/PASSWORD/FULL_NAME`.
- `time.sleep()` hardcode thay bằng `settings.GEMINI_RETRIEVAL_EMBED_RETRY_MIN_WAIT`.
- `flush_langfuse()` trong khối `finally` đảm bảo traces được đẩy hoàn chỉnh lên Langfuse Cloud trước khi script kết thúc.
- `backend/app/seed_data.py` — file proxy đơn giản hỗ trợ `python -m app.seed_data`.

---

## Quyết định kỹ thuật quan trọng (Sprint 15, 16, 16.5 & 16.6)
- **Không hỗ trợ tùy biến difficulty**: Hệ thống loại bỏ trường `difficulty` khỏi API request schema và UI. Độ phân cấp câu hỏi được kiểm soát bởi system instruction Bloom cố định của Backend.
- **Trường computed `total_items`**: Không lưu trên physical database column để tránh không đồng nhất dữ liệu.
- **Không dùng Redis/Celery**: Rate limiting và quota được thực thi nhẹ bằng cách check trực tiếp dữ liệu DB & ghi in-memory hoặc lock cooldown theo timestamp của user. FE hỗ trợ disable nút submit khi đang pending.
- **Scope giới hạn**: Enum `ArtifactType` có mặt cả FLASHCARD và SUMMARY nhưng code của Sprint 15/16 chỉ hỗ trợ sinh và hiển thị danh mục QUIZ. Không có bất kỳ giao diện hay API riêng cho các loại hình khác.
- **Migrations tối giản**: Sử dụng `create_all()` + reseed data trên local/dev. Không tạo thêm file migration Alembic nào cho `NotebookArtifact` trong sprint này.

## Local-First & Cloud-Ready

Toàn bộ pipeline chạy được hoàn toàn ở local (Docker Compose: PostgreSQL 16 + pgvector, MinIO, backend có LibreOffice headless), chỉ cần một API key Gemini trong `.env`. Khi deploy, đổi các biến môi trường sang dịch vụ cloud tương ứng (Postgres managed, object storage S3-compatible, Cloudmersive API) — không phải sửa code.

---

# 14. Development Workflow

Planning → Implementation → Testing → Documentation → Commit → Push GitHub

---

# 15. Git Convention

Commit theo Sprint hoặc feature, ví dụ `feat: implement upload module`. Tránh message chung chung như `update` hoặc `fix`.

---

# 16. AI Collaboration Instructions

- Đọc code hiện tại trước khi cập nhật documentation hoặc đề xuất thay đổi.
- Giữ giải pháp đơn giản, phù hợp đồ án đại học và giới hạn thời gian/ngân sách.
- Không mô tả planned feature là đã triển khai; phân biệt rõ code hiện tại với roadmap.
- Khi kiến trúc thay đổi, cập nhật các tài liệu liên quan trong `docs/`, không chỉ file này.

---

# 17. Current Status

Current Status: **Sprint 17 — Testing** (đang triển khai)

Last Completed: **Sprint 16.6 — Centralized Settings & LLMOps Observability Hardening** — hoàn thành.

Highlights of last completed sprint:
- **22+ Pydantic Settings fields** tập trung toàn bộ config AI pipeline trong `config.py`; không còn magic number nào trong service layer.
- **Langfuse v4.15.1 compatibility**: `observability.py` tự động detect v4 (`from langfuse import observe, get_client`) vs v2/v3 fallback; `_IS_LANGFUSE_ENABLED = True` đã xác nhận hoạt động.
- **Tracing coverage đầy đủ**: document ingestion pipeline, embeddings batch, query embedding, quiz generation đều có `@observe_llm` span; seed_data CLI flush traces trước khi thoát.
- **Test Suite**: 11/11 tests PASSED (100%) trên Python 3.12.

Next Module: Sprint 17 — Testing (Đánh giá Thực nghiệm Ragas) và Sprint 18 — Deployment & Optimization.

Nguyên tắc vận hành từ Sprint 11.5 trở đi: mỗi sprint phải tự kiểm thử độc lập và chạy xanh trước khi mở sprint kế tiếp; các sprint backend (11.5, 12, 13, 15, 16.5, 16.6) có script test độc lập, phần giao diện chat và quiz tương ứng tách sang Sprint 14 và Sprint 16.

---

# 18. Notes

Ưu tiên cân bằng System Core và AI/RAG, nhưng không over-engineer vượt quá khả năng hoàn thành của đồ án cá nhân.

---

# 19. Idea Backlog / Future Considerations

## 19a. Backlog kỹ thuật & Nợ kỹ thuật đang mở

### Hoãn vô thời hạn

- ~~**Deduplication theo SHA-256:**~~ **ĐÃ TRIỂN KHAI (Sprint 16.5)** — SHA-256 `file_hash` lưu khi upload; khi ingest phát hiện hash trùng, tái sử dụng toàn bộ `AssetEmbedding` sẵn có (không gọi Gemini API, tiết kiệm 100% chi phí embedding).
- **Reranker (Cross-Encoder):** Hoãn vô thời hạn / Idea Backlog - Nhằm ưu tiên độ trễ (latency) thấp và vì tập dữ liệu (dataset) tài liệu nhỏ của đồ án cá nhân, hệ thống không tích hợp mô hình Reranker phân cấp dạng Cross-Encoder. Truy hồi Hybrid RRF Top-5 là đủ đáp ứng chất lượng.

### Nợ kỹ thuật tồn đọng từ audit Sprint 7

> Nhóm này **xử lý riêng ở một giai đoạn sau**, cố ý **không gộp vào các sprint RAG (11.5 → 15)** để không làm loãng phạm vi và giữ nguyên khả năng kiểm thử độc lập từng sprint.

- **C6:** xử lý `id` không hợp lệ (route param không phải số / không tồn tại) — hiện chưa trả lỗi nhất quán.
- **K5 / K7 / E9:** còn `id` hardcode và một số bộ lọc đang thực hiện phía client thay vì đẩy xuống query backend.
- **H1–H5:** dead code và đoạn logic trùng lặp cần dọn.
- **Chuẩn hóa i18n EN/VI:** vẫn còn chỗ hiển thị raw enum tiếng Anh xen với label tiếng Việt.

### Dự phòng mở rộng

- Hỗ trợ thêm định dạng **PPTX / EPUB** (LibreOffice headless đã convert được PPTX → PDF nên chi phí mở rộng thấp).
- **Quản lý chi phí token:** giới hạn token/request, cache câu trả lời và quota theo user/session.
- Virus scanning và presigned upload/download URL.
- AI artifact layer (summary, mindmap) mở rộng từ nền tảng quiz/flashcards của Sprint 15.
- **Nâng cấp Chat AI Agent (Tool Calling):** Tái sử dụng `quiz_service.generate_quiz()` độc lập của Sprint 15 để bọc thành Function Declaration (Tool Calling) cho Gemini Chat Engine. Cho phép người dùng ra lệnh bằng ngôn ngữ tự nhiên ngay trong khung chat (ví dụ: *"Tạo 5 câu trắc nghiệm cho tài liệu vừa thảo luận"*) để LLM tự kích hoạt sinh đề và hiển thị kết quả trực tiếp.

## 19b. Quan sát UI/UX & cấu trúc code (sẽ xử lý ở Sprint 9, sau khi hoàn tất Sprint 8.5)

- **HomePage:** Có hai lối browse song song — `TaxonomyView` (widget 3 bước) và khối "Bắt đầu nhanh" + nav "Duyệt theo khoa" dẫn tới `/departments`; trải nghiệm trùng lặp, chưa thống nhất một entry point duy nhất. *(Sau Sprint 8.5 sẽ thay bằng lưới Card Department theo Progressive Disclosure — xem 19c.)*
- **PublicLayout:** Thanh nav gom nhiều link (browse, trang chủ, tài liệu, đóng góp, admin, user) trên một hàng — dễ chật trên viewport hẹp, chưa có responsive collapse/menu.
- **Browse pages (`DepartmentsPage`, `DepartmentDetailPage`, `MajorDetailPage`, `SubjectDetailPage`):** Cùng pattern `max-w-5xl px-6 py-12` nhưng link "Quay lại" không nhất quán (một số về `/`, một số về `/departments`, `MajorDetailPage` về khoa cha).
- **ResourceDetailPage:** Badge hiển thị raw enum tiếng Anh (`resource_type`, `status` — ví dụ `DOCUMENT`, `READY`) trong khi các trang khác đã Việt hóa label.
- **ResourceUploadPage:** Badge visibility vẫn hiển thị raw enum (`PRIVATE`, `PENDING_REVIEW`) thay vì label tiếng Việt như `MyResourcesPage`. *(Trang này gắn với luồng Resource cũ — sẽ đổi/ẩn theo mục 19c khi Admin tạm dừng.)*
- **MyResourcesPage vs SubjectDetailPage:** Card resource khác layout hoàn toàn — grid 2 cột có badge/reject/upload (cá nhân) vs list link đơn giản (công khai qua `PublicResourceCard`); hợp lý về nghiệp vụ nhưng chưa có design system thống nhất.
- **ResourceCreatePage:** Form dùng raw `<input>`/`<select>` Tailwind inline; **Login/Register** dùng shared `Input`/`Button` — không đồng nhất component form. *(Trang này gắn với luồng đóng góp cũ — sẽ ẩn/thay theo Google Form ở mục 19c.)*
- **AdminModerationPage / AdminTaxonomyPage:** Nội dung admin nằm trong card trắng giống AppLayout pages, nhưng markup JSX bị nén một dòng ở bảng/modal (`AdminTaxonomyPage`) — khó đọc và khó chỉnh spacing từng cell.
- **AdminTaxonomyPage:** Bảng HTML thuần không có zebra/hover rõ, modal form dày đặc, thiếu empty-state illustration nhất quán với trang public.
- **AppLayout vs PublicLayout:** Link admin xuất hiện ở cả nav ngang (`AdminNavLinks`) và sidebar AppLayout — admin thấy hai cách vào cùng chức năng tùy layout đang ở.

> Các mục liên quan tới Admin/luồng đóng góp cũ ở trên **tạm hoãn xử lý** trong lúc nhánh Admin dừng phát triển (mục 19c). Chỉ quay lại polish khi/nếu nhánh Admin được làm tiếp vào cuối đồ án.

## 19c. Sprint 8.5 — Database Architecture Refactor ✅ **HOÀN THÀNH**

> Toàn bộ kế hoạch trong mục này đã được triển khai. Xem mục 4, 7, 8, 17 để biết trạng thái code thật.

### Lý do

Bảng `Resource` cũ dùng chung cho cả tài liệu Public (học liệu kiểu Studocu) và Workspace AI cá nhân (kiểu NotebookLM) gây xung đột: Public cần lưu trọn bộ slide bài giảng (10–15 file, không giới hạn), trong khi Private Workspace bắt buộc giới hạn số nguồn rất khắt khe để bảo vệ chi phí/token AI RAG và tránh quá tải context window. Quyết định tách hoàn toàn 2 domain thành DB riêng thay vì che bằng giao diện Frontend.

### Kiến trúc dữ liệu mới

**`Document`** — Tài liệu Public (thư viện dùng chung)
- Gắn chặt với `Subject` (bắt buộc).
- Thuộc tính: `id`, `title` (bắt buộc), `description` (tùy chọn), `subject_id` (FK bắt buộc), `resource_type` (enum: `EXAM`, `SLIDE`, `DOCUMENT`... — gom nhóm hiển thị UI), `status` (enum: `DRAFT`, `PUBLIC`, `DELETED` — **giữ 3 giá trị, không thêm `PENDING_REVIEW` ngay** vì đăng bài giờ qua seed trực tiếp ra `PUBLIC`, không qua duyệt), `created_by` (FK Admin/user tạo).
- Không giới hạn số lượng file.

**`Notebook`** — Không gian AI cá nhân (Private Workspace)
- Gắn với `User` (bắt buộc).
- Thuộc tính: `id`, `title` (bắt buộc), `owner_id` (FK bắt buộc), `subject_id` (nullable — chỉ để gợi ý tài liệu liên quan sau này).

**`Asset`** — Quản lý file vật lý
- Bỏ cột `resource_id`.
- Thêm 2 FK nullable: `document_id`, `notebook_id`.
- Quy tắc Service Layer: 1 Asset chỉ gắn `Document` **HOẶC** `Notebook` — không đồng thời, không để trống cả hai. Đảm bảo xóa Notebook cá nhân không vô tình mất file hệ thống công cộng.

**`Notebook_Saved_Documents`** — bảng liên kết logic
- Khi user lưu 1 `Document` public vào `Notebook` để chat RAG, **không nhân bản file vật lý** trên MinIO, chỉ tạo record liên kết logic (`notebook_id`, `document_id`).

**`AssetEmbedding`** — bảng vector cho RAG *(đề xuất thêm ngoài bản thảo gốc, mới ở mức ý tưởng logic, chưa có thiết kế kỹ thuật chi tiết chunking/dimension/index — cần làm rõ khi thật sự triển khai AI Pipeline)*
- Khóa ngoại tới `asset_id` (không phải `notebook_id`), vì `Asset` đã là tầng file dùng chung.
- RAG truy vấn cho 1 Notebook sẽ gom 2 nguồn: (a) Asset thuộc chính Notebook (`notebook_id = X`), (b) Asset thuộc Document đã lưu qua `Notebook_Saved_Documents`.
- → Document public chỉ embed 1 lần dù nhiều Notebook cùng lưu, đúng tinh thần tiết kiệm token ban đầu.

**Quota Notebook** (gộp thành 1 quota duy nhất)
- `MAX_SOURCES_PER_NOTEBOOK` = 10 (mặc định) — áp dụng chung cho tổng cả tài liệu lưu từ thư viện công cộng (Document) và tệp cá nhân tự upload (Asset) cộng lại (không có giới hạn phụ riêng cho từng loại). Để dạng config, dễ điều chỉnh sau này.

**Background Worker dọn file rác**
- Khi `Document` bị xóa mềm (`status = DELETED`), Postgres vẫn giữ text/metadata để lưu vết, chống spam, phục vụ audit; worker ngầm xóa file vật lý trên MinIO sau **30 ngày**.
- Áp dụng logic tương tự cho `Asset` thuộc `Notebook` khi user tự xóa file, để nhất quán giữa 2 domain.

### Contribution Flow MVP (điều chỉnh — tạm dừng Admin)

- Dùng **Google Forms** để nhận đóng góp tài liệu Public từ người dùng thay vì tự code upload/duyệt phía Frontend — tránh chi phí MinIO, rủi ro bảo mật/virus scan, lập trình preview PDF/DOCX, khối lượng code Frontend (progress bar, timeout, trang duyệt admin...).
- **Nhánh Admin (form/API tạo Document) tạm dừng phát triển** — không code thêm, **không xóa code cũ** của các sprint trước (API + FE admin cũ vẫn giữ nguyên trong repo, mở lại/demo được bất cứ lúc nào).
- **Không đổi kế hoạch gần**: tạm dừng qua hết Sprint 8.5/9/10. Nếu còn dư thời gian ở giai đoạn cuối đồ án, sẽ quay lại hoàn thiện tiếp nhánh Admin + đóng góp tài liệu (dự tính ban đầu là sẽ làm tiếp nếu kịp thời gian).
- **Cách đăng data Public trong lúc admin tạm dừng**: mở rộng `seed.py` sẵn có để chèn Document mẫu thật, đủ dùng demo và phát triển tiếp Sprint 9 — không cần viết CLI/tool riêng.
- Khi cần mở lại luồng đóng góp/duyệt trực tiếp trên web trong tương lai: thêm `PENDING_REVIEW` vào enum `status` bằng 1 Alembic migration riêng lúc đó, và bật lại nhánh Admin đã có sẵn.

### Luồng trải nghiệm Frontend (Progressive Disclosure)

1. **HomePage** — bỏ widget chọn 3 bước cũ, thay bằng lưới Card **Department**, có nút đóng góp nhanh dẫn qua Google Form.
2. **DepartmentDetailPage** — click Department → danh sách **Major**.
3. **MajorDetailPage** — click Major → danh sách **Subject** dạng Accordion.
4. **SubjectDetailPage** — click Subject → danh sách **Document** công khai, gom nhóm theo `resource_type` (SLIDE, EXAM...) thay vì rải Asset vật lý ra ngoài. Click 1 dòng Document → trang chi tiết để tải file.

### Kế hoạch thực hiện

**Sprint 8.5 (Backend):** Sửa SQLAlchemy models/Schemas cho `Document`/`Notebook`/`Asset`/`Notebook_Saved_Documents`/`AssetEmbedding`; viết API mới `/documents` `/notebooks` (làm luôn download/presigned URL theo `asset_id` mới, không nợ sang Sprint 10); Alembic migration (không cần migrate data cũ, xóa và seed lại từ đầu); mở rộng `seed.py`.

**Sprint 8.5 (Frontend, chỉ dọn tạm):** đổi hook `useResources` → `useDocuments`/`useNotebooks`, cập nhật TS interfaces; ẩn/comment nút upload public cũ + form tạo Document phía Admin. Mục tiêu duy nhất: app chạy lại được, không lỗi build, chưa cần đẹp.

**Sau Sprint 8.5:** refactor lại API BE/FE liên quan cho chuẩn (không dừng ở mức dọn tạm) để chuẩn bị tốt cho Sprint tiếp theo, tránh để nợ kỹ thuật — rồi mới vào Sprint 9 (UI/UX Polish, mục 12) theo chiến lược bottom-up: Giai đoạn 1 chuẩn hóa component dùng chung `src/components/ui/` + layout; Giai đoạn 2 lắp component vào từng trang theo đúng luồng khám phá mới (Home → Department → Major → Subject → chi tiết Document).