```markdown
# PROJECT CONTEXT — NỀN TẢNG CHIA SẺ HỌC LIỆU TÍCH HỢP AI/RAG (V1.3 - SPRINT 7 FE CATCH-UP COMPLETE)

## 1. Bối cảnh & Tầm nhìn Dự án

Tôi đang làm **đồ án ngành** với đề tài:

> **Xây dựng nền tảng chia sẻ học liệu, tích hợp các tính năng AI để hỗ trợ học tập.**

Ý tưởng ban đầu được lấy cảm hứng từ các nền tảng như **Studocu**, nhưng mục tiêu không phải sao chép toàn bộ scope cộng đồng của Studocu (như Karma points, Paywall, Chat thời gian thực...).

Dự án tập trung vào **Độ sâu Kiến trúc (Architecture Depth)** và **Tích hợp AI/RAG cá nhân hóa**, được chia làm 2 phân vùng cốt lõi (Dual-Zone Architecture):

```text
               NỀN TẢNG HỌC LIỆU INTEGRATED AI
                             │
       ┌─────────────────────┴─────────────────────┐
       ▼                                           ▼
1. PUBLIC RESOURCE HUB                     2. PERSONAL WORKSPACE
(Phạm vi: Toàn trường / Demo 1 Khoa)        (Phạm vi: Cá nhân người dùng)
─────────────────────────────               ─────────────────────────────
• Quản lý & Chia sẻ học liệu               • Lưu trữ ghi chú / tài liệu riêng tư
• Tổ chức tập trung theo Môn/Khoa           • AI Assistant / RAG trên tài liệu cá nhân
• Phân quyền xem / Tải về / Tìm kiếm        • Tự động tạo Quiz / Summary / Q&A

```

**Cơ chế Bridge Flow:** Cho phép chuyển đổi tài liệu cá nhân trong Workspace thành tài liệu chia sẻ công khai lên Public Hub chỉ bằng cách thay đổi thuộc tính `visibility` (không duplicate dữ liệu).

---

## 2. Technology Stack

### Đã quyết định — đang dùng trong project

* **Frontend:** React + Vite + TypeScript + Tailwind CSS + React Router + Axios + react-hook-form
* **Backend:** FastAPI (Python)
* **Database:** PostgreSQL + `pgvector` extension (lưu cả dữ liệu quan hệ lẫn embeddings)
* **Storage:** MinIO (local dev qua Docker Compose)
* **AI Integration:** LangChain, OpenAI API, Sentence Transformers, pgvector (mô hình cụ thể — ví dụ embedding model, LLM model — chưa chốt, sẽ quyết định ở Sprint 8)

### Tham khảo cho tương lai — chưa quyết định, chưa áp dụng

Đây là các khuyến nghị công nghệ chung từ tài liệu gợi ý đề tài của GVHD (không phải quyết định riêng đã chốt cho project này), giữ lại làm tham khảo cho các sprint chưa tới:

* **Testing:** `pytest` (BE), `Jest`/`Playwright` (FE) — cân nhắc áp dụng ở Sprint 11 Testing
* **DevOps:** GitHub Actions (CI), Vercel (FE Deployment), Railway/Render (BE Deployment) — cân nhắc áp dụng ở Sprint 12 Deployment & Optimization

### Quy trình & chuẩn deliverable theo GVHD

Project là đề tài tự đề xuất đã được GVHD duyệt (không thuộc danh sách đề tài mẫu). Các yêu cầu quy trình cần tuân theo: deploy chạy thật (không chỉ chạy local), có kiểm thử, tài liệu chuyên nghiệp, mã nguồn GitHub sạch với commit history rõ ràng.

---

## 3. Kiến trúc Học liệu & Không gian Học tập (Document & Notebook Abstraction Layer)

Để giải quyết hạn chế của việc phân mảnh dữ liệu và tách biệt giữa các khu vực, từ Sprint 8.5 hệ thống tách biệt luồng lưu trữ học liệu thành hai phân vùng:

* Bảng `Document` đại diện cho các học liệu công khai chia sẻ trên Public Hub.
* Bảng `Notebook` đại diện cho các ghi chú, tài liệu nghiên cứu cá nhân bên trong Workspace.
* Bảng `Asset` đại diện cho lớp lưu trữ tệp vật lý thực tế trên MinIO.
* `Asset` liên kết với `Document` hoặc `Notebook` bằng cách dùng 2 trường nullable: `document_id` và `notebook_id` kèm theo một ràng buộc loại trừ lẫn nhau `CHECK ((document_id IS NULL) != (notebook_id IS NULL))` (XOR constraint). Trong MVP hiện tại, Document đi kèm đúng 1 Asset (quan hệ 1:1).

```text
Document (Public Hub)
├── id, title, description
├── resource_type (Enum: LECTURE, EXAM, REFERENCE, SYLLABUS...)
├── subject_id, owner_id
└── status (Enum: DRAFT, PUBLIC, DELETED)

Notebook (Private Workspace)
├── id, title, owner_id
└── visibility (Enum: PRIVATE, PENDING_REVIEW, PUBLIC)

Asset (Physical Storage)
├── id
├── document_id (XOR with notebook_id)
├── notebook_id (XOR with document_id)
├── file_name, file_path
├── file_type, size
└── storage target: MinIO
```


```

**Chiến lược MVP (Extensible Architecture, Focused MVP):**

* **Phase 1 (MVP):** Thiết kế schema hỗ trợ đa định dạng, nhưng chỉ triển khai upload/chạy pipeline cho tài liệu dạng document trước.
* **Mở rộng tương lai:** Khi thêm `Audio`, `Video` hay AI-generated artifacts, chỉ cần bổ sung extractor/producer mới, không thay đổi Core DB hay API contract cũ.

---

## 4. AI Universal Processing Pipeline (Planned)

Toàn bộ luồng xử lý AI được thiết kế độc lập với nguồn học liệu ban đầu thông qua bước **Text Normalization**:

```text
[PDF File]   ──(PDF Extractor)──┐
                                 ├─► [Normalized Text] ─► [Chunking] ─► [Embedding] ─► [pgvector DB]
[Audio File] ──(Whisper/STT)────┘
                                                                                            │
[User Query] ───────────────────► [Vector Search & RAG] ◄──────────────────────────────────┘


```

* AI Layer (`Chunks` & `Embeddings`) chỉ làm việc trên `Normalized Text`.
* Bảng `document_chunks` và embedding schema chưa tồn tại trong code hiện tại; đây là thiết kế dự kiến cho Sprint 8+.
* Khi hỏi AI trong **Workspace cá nhân**: Query filter theo `user_id` hoặc `resource_id`.
* Khi hỏi AI trên **Public Hub**: Query filter theo `subject_id` và `visibility = 'PUBLIC'`.

---

## 5. Chiến lược Mở rộng Không Phá Vỡ Core (Extensibility Strategy)

Dự án ưu tiên hoàn thiện **Core System + AI Layer (MUST HAVE & SHOULD HAVE)**. Các tính năng như **Karma (Điểm thưởng)** hay **Payment (VNPay/VIP Plan)** được xếp vào nhóm **COULD HAVE** và được thiết kế theo dạng **Loose Coupling (Ghép nối lỏng)**:

* **Core Tables (`users`, `resources`, `assets`, `subjects`):** Đứng hoàn toàn độc lập, không chứa các cột như `is_vip` hay `karma_points`.
* **Module Mở Rộng (Nếu thêm sau):** Tạo các bảng vệ tinh mới (`subscriptions`, `user_points`) kết nối qua `user_id` Foreign Key.
* **Tích hợp Code:** Dùng Middleware / Custom Dependency (`require_vip_user`) và Event/Background Tasks trong FastAPI để cắm module mở rộng vào mà không sửa logic Core.

---

## 6. Mô hình Phân quyền & User Roles

Sử dụng mô hình **User + Role** trên một bảng `users` duy nhất:

* `USER`: role mặc định; có thể tạo resource, xem resource của mình, upload asset và submit resource của mình để review.
* `PREMIUM_USER`: enum đã có nhưng hiện chưa có quyền riêng trong code.
* `ADMIN`: quản lý danh mục học thuật, approve resource pending review, cập nhật và soft-delete resource.

Khi tạo, user thường có thể để mặc định `PRIVATE` hoặc truyền `PENDING_REVIEW` để đóng góp trực tiếp vào hàng chờ duyệt; chỉ `ADMIN` được truyền `PUBLIC` trực tiếp. Luồng review từ resource private là `PRIVATE → PENDING_REVIEW → PUBLIC`. Public list/detail chỉ hiển thị resource `PUBLIC` chưa có status `DELETED`.

---

## 7. Các bước Thực thi tiếp theo (Execution Plan)

Chuyển hoàn toàn sang giai đoạn **Code & Design Chi Tiết**:

```text
1. ✅ Thiết kế Database Schema (SQLAlchemy Models)
        ↓
2. ✅ Setup Repository & Docker Compose (PostgreSQL + pgvector + MinIO)
        ↓
3. ✅ Xây dựng API Auth, Academic Structure, Resource và Upload
        ↓
4. ✅ Triển khai Service Upload & File Validation (PDF/DOCX → MinIO); PDF Extraction chưa có
        ↓
5. ✅ Triển khai Frontend UI shell (React + TS) & Kết nối auth thật
        ↓
6. ✅ FE Catch-up Features — nối API thật (browse, /me/resources, upload, moderation, admin taxonomy)
        ↓
7. ✅ Sprint 8.5/9 Cleanup: Document/Notebook split, Quota adjustments, Search & PDF Preview
        ↓
8. 🟢 Triển khai AI Layer (Chunking, Embedding, Vector Search & RAG Q&A) — chưa bắt đầu
```

---

## PROMPT MANG SANG CHAT MỚI (NẾU CẦN)

> "Tôi đang xây dựng đồ án ngành 'Nền tảng chia sẻ học liệu tích hợp AI/RAG' theo file PROJECT_CONTEXT.md. Backend đã hoàn thành Sprint 5; Frontend đã hoàn thành Sprint 6–7 (auth, browse flow, personal resources, upload/submit-review, admin moderation/taxonomy). Hãy đọc code hiện tại trước, sau đó giúp tôi triển khai Sprint kế tiếp theo scope đã xác nhận."

---

## Scope of Implementation & Future Enhancements

Đồ án được phát triển theo hướng **Core First**.

Trong giai đoạn đầu (MVP), mục tiêu là hoàn thiện đầy đủ các chức năng cốt lõi của hệ thống, bao gồm quản lý học liệu, phân quyền người dùng, AI Pipeline và RAG trên tài liệu.

Sau khi Core System ổn định, nếu còn thời gian trong quá trình thực hiện đồ án, hệ thống sẽ tiếp tục được mở rộng với các tính năng nâng cao đã được tính đến ngay từ giai đoạn thiết kế kiến trúc.

### Core Features (MVP)

* Authentication & Authorization
* Academic Structure Management
* Learning Resource Management
* Personal Workspace
* AI Pipeline (Chunking, Embedding, Vector Search) — planned
* RAG Question Answering — planned
* Public Resource Hub

### Sprint 6 Delivered Scope

* Frontend foundation hoàn tất: Vite + React + TypeScript + Tailwind
* Auth flow thật hoạt động với backend: register/login/logout, token persistence, protected/admin routes
* Routing shell và layout cho public/protected/admin area

### Sprint 7 Delivered Scope

* TanStack Query + react-hot-toast; shared UI (`Spinner`, `ErrorMessage`, `PaginationBar`)
* Browse flow công khai: Departments → Major → Subject → Resource detail
* `/me/resources`, create → upload → submit-review; admin moderation và admin taxonomy CRUD
* Backend bổ sung: filter taxonomy (`department_id`, `major_id`), `GET /resources/me/{id}`, `GET /resources/admin`
* Các màn hình core đã nối API thật end-to-end (không còn mock UI cho luồng chính)

### Sprint 8.5 & 9 Delivered Scope (Cleanup & AI Prep)

* **Document / Notebook Architecture split:** Tự động tách `Resource` cũ thành `Document` (chia sẻ) và `Notebook` (Workspace), dọn sạch references và types.
* **Subject Search API & Dropdown:** Hỗ trợ tìm kiếm môn học tức thì không phân biệt dấu tại Header.
* **PDF Preview Modal:** Hỗ trợ preview tệp văn bản PDF từ CDN Presigned URL của MinIO.
* **Flat Document List:** Tối giản hóa danh mục tài liệu theo luồng ngang, loại bỏ Card trung gian.

### Planned Future Enhancements

Các tính năng dưới đây **không bị loại bỏ khỏi định hướng phát triển**, mà chỉ được ưu tiên triển khai sau khi hoàn thành Core System:

* Karma / Reward System
* Premium Subscription & Payment Integration
* Real-time Notifications / Chat
* Recommendation System
* Learning Analytics Dashboard
* Flashcards & Quiz Generation nâng cao
* Mobile Application
* Distributed Architecture / Microservices (nếu cần mở rộng quy mô)

Việc triển khai các tính năng trên sẽ phụ thuộc vào thời gian còn lại của đồ án và mức độ hoàn thiện của hệ thống cốt lõi.

```

```