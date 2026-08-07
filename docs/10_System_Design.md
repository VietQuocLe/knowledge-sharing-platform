````markdown
# PROJECT CONTEXT — NỀN TẢNG CHIA SẺ HỌC LIỆU TÍCH HỢP AI/RAG (V1.1 - RESTRUCTURED)

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
````

**Cơ chế Bridge Flow:** Cho phép chuyển đổi tài liệu cá nhân trong Workspace thành tài liệu chia sẻ công khai lên Public Hub chỉ bằng cách thay đổi thuộc tính `visibility` (không duplicate dữ liệu).

---

## 2. Công nghệ đã thống nhất với GVHD

- **Frontend:** ReactJS + TypeScript + React Router (Không dùng Next.js)
- **Backend:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL + `pgvector` extension (Lưu cả dữ liệu quan hệ lẫn Embeddings)
- **Storage:** Object Storage (MinIO ở Local Dev, sẵn sàng chuyển AWS S3/Cloudflare R2 trên Prod)
- **AI Integration:** LangChain / LlamaIndex + OpenAI API (`text-embedding-3-small`, `gpt-4o-mini`)
- **Testing:** `pytest` (BE), `Jest` (FE), `Playwright` (E2E)
- **DevOps:** Docker Compose (Local DB & MinIO), GitHub Actions (CI), Vercel (FE Deployment), Railway/Render (BE Deployment)

---

## 3. Kiến trúc Học liệu Trừu tượng (Resource Abstraction Layer)

Để giải quyết hạn chế của các đồ án cũ (chỉ lưu được file PDF/Word cố định), hệ thống áp dụng pattern **Abstraction Layer**:

- Bảng cốt lõi là `Resource` thay vì `documents`.
- `Resource` giữ siêu dữ liệu học liệu và liên kết tới một hoặc nhiều `Asset` vật lý.
- Sử dụng cột `resource_type` (Enum: `DOCUMENT`, `VIDEO`, `AUDIO`, `LINK`, `AI_ARTIFACT`) kết hợp với cột **`metadata_json` (PostgreSQL `JSONB`)** để lưu trữ thuộc tính động của từng loại học liệu mà không cần đổi Database Schema khi mở rộng.

```text
Resource
├── id, title, description
├── resource_type (DOCUMENT | VIDEO | AUDIO | LINK | AI_ARTIFACT)
├── metadata_json (JSONB: ngôn ngữ, học kỳ, tác giả, source...)
├── subject_id, owner_id
└── assets (0..n)

Asset
├── id, resource_id
├── file_name, file_path
├── file_type, version, size
└── storage target: MinIO / S3 / external link

```

**Chiến lược MVP (Extensible Architecture, Focused MVP):**

- **Phase 1 (MVP):** Thiết kế schema hỗ trợ đa định dạng, nhưng chỉ triển khai upload/chạy pipeline cho tài liệu dạng document trước.
- **Mở rộng tương lai:** Khi thêm `Audio`, `Video` hay AI-generated artifacts, chỉ cần bổ sung extractor/producer mới, không thay đổi Core DB hay API contract cũ.

---

## 4. AI Universal Processing Pipeline

Toàn bộ luồng xử lý AI được thiết kế độc lập với nguồn học liệu ban đầu thông qua bước **Text Normalization**:

```text
[PDF File]   ──(PDF Extractor)──┐
                                 ├─► [Normalized Text] ─► [Chunking] ─► [Embedding] ─► [pgvector DB]
[Audio File] ──(Whisper/STT)────┘
                                                                                            │
[User Query] ───────────────────► [Vector Search & RAG] ◄──────────────────────────────────┘

```

- AI Layer (`Chunks` & `Embeddings`) chỉ làm việc trên `Normalized Text`.
- Bảng `document_chunks` chứa `resource_id`, `user_id`, `text_content` và `embedding_vector`.
- Khi hỏi AI trong **Workspace cá nhân**: Query filter theo `user_id` hoặc `resource_id`.
- Khi hỏi AI trên **Public Hub**: Query filter theo `subject_id` và `visibility = 'PUBLIC'`.

---

## 5. Chiến lược Mở rộng Không Phá Vỡ Core (Extensibility Strategy)

Dự án ưu tiên hoàn thiện **Core System + AI Layer (MUST HAVE & SHOULD HAVE)**. Các tính năng như **Karma (Điểm thưởng)** hay **Payment (VNPay/VIP Plan)** được xếp vào nhóm **COULD HAVE** và được thiết kế theo dạng **Loose Coupling (Ghép nối lỏng)**:

- **Core Tables (`users`, `resources`, `assets`, `subjects`):** Đứng hoàn toàn độc lập, không chứa các cột như `is_vip` hay `karma_points`.
- **Module Mở Rộng (Nếu thêm sau):** Tạo các bảng vệ tinh mới (`subscriptions`, `user_points`) kết nối qua `user_id` Foreign Key.
- **Tích hợp Code:** Dùng Middleware / Custom Dependency (`require_vip_user`) và Event/Background Tasks trong FastAPI để cắm module mở rộng vào mà không sửa logic Core.

---

## 6. Mô hình Phân quyền & User Roles

Sử dụng mô hình **User + Role** trên một bảng `users` duy nhất:

- `STUDENT`: Upload tài liệu vào Workspace, publish lên Public Hub, chat RAG.
- `LECTURER`: Upload học liệu chính thống, phê duyệt tài liệu.
- `ADMIN`: Quản lý danh mục môn học, kiểm duyệt nội dung (Moderation).

---

## 7. Các bước Thực thi tiếp theo (Execution Plan)

Chuyển hoàn toàn sang giai đoạn **Code & Design Chi Tiết**:

```text
1. Thiết kế Chi tiết Database Schema (SQLAlchemy Models)
        ↓
2. Setup Repository & Docker Compose (PostgreSQL + pgvector + MinIO)
        ↓
3. Xây dựng Restful API Spec cho Auth & Resource Management
        ↓
4. Triển khai Service Upload & Background Task Processing (PDF Extraction)
        ↓
5. Triển khai AI Layer (Chunking, Embedding, Vector Search & RAG Q&A)
        ↓
6. Xây dựng Frontend UI (ReactJS + TS) & Kết nối API

```

---

## PROMPT MANG SANG CHAT MỚI (NẾU CẦN)

> "Tôi đang xây dựng đồ án ngành 'Nền tảng chia sẻ học liệu tích hợp AI/RAG' theo file context PROJECT_CONTEXT.md. Chúng tôi đã chốt xong toàn bộ Architecture, Dual-Zone Boundary (Public Hub & Personal Workspace), Resource Abstraction Layer với PostgreSQL JSONB, và AI Pipeline.
> Với vai trò Tech Lead/System Architect, hãy dẫn dắt tôi triển khai bước thực tế tiếp theo: Viết file SQLAlchemy Models (`models.py`) đầy đủ và chuẩn hóa cho toàn bộ cơ sở dữ liệu của hệ thống (Auth, Academic Structure, Learning Resources & RAG Chunks)."

```

---

Bản tái cấu trúc này đã cô đọng mọi góc nhìn kiến trúc nâng cao nhất của m. M có thể lưu lại ngay để làm tài liệu gốc nhé!

```

## Scope of Implementation & Future Enhancements

Đồ án được phát triển theo hướng **Core First**.

Trong giai đoạn đầu (MVP), mục tiêu là hoàn thiện đầy đủ các chức năng cốt lõi của hệ thống, bao gồm quản lý học liệu, phân quyền người dùng, AI Pipeline và RAG trên tài liệu.

Sau khi Core System ổn định, nếu còn thời gian trong quá trình thực hiện đồ án, hệ thống sẽ tiếp tục được mở rộng với các tính năng nâng cao đã được tính đến ngay từ giai đoạn thiết kế kiến trúc.

### Core Features (MVP)

- Authentication & Authorization
- Academic Structure Management
- Learning Resource Management
- Personal Workspace
- AI Pipeline (Chunking, Embedding, Vector Search)
- RAG Question Answering
- Public Resource Hub

### Planned Future Enhancements

Các tính năng dưới đây **không bị loại bỏ khỏi định hướng phát triển**, mà chỉ được ưu tiên triển khai sau khi hoàn thành Core System:

- Karma / Reward System
- Premium Subscription & Payment Integration
- Real-time Notifications / Chat
- Recommendation System
- Learning Analytics Dashboard
- Flashcards & Quiz Generation nâng cao
- Mobile Application
- Distributed Architecture / Microservices (nếu cần mở rộng quy mô)

Việc triển khai các tính năng trên sẽ phụ thuộc vào thời gian còn lại của đồ án và mức độ hoàn thiện của hệ thống cốt lõi.