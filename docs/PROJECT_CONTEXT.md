# PROJECT_CONTEXT.md

# Knowledge Sharing Platform

> Graduation Project — AI-powered Knowledge Sharing Platform inspired by Studocu + NotebookLM

---

# 1. Project Overview

## Description

Knowledge Sharing Platform là hệ thống chia sẻ học liệu kết hợp AI. Mục tiêu là xây dựng nền tảng tổ chức học liệu theo Khoa → Ngành → Môn học, cho phép người dùng tạo resource cá nhân, upload tài liệu và đưa tài liệu qua quy trình kiểm duyệt để chia sẻ công khai. AI/RAG và notebook cá nhân là các phase tiếp theo.

---

# 2. Current Progress

Current Sprint

> Sprint 6 — AI Pipeline

Overall Progress

80%

Status

✅ Sprint 5 Completed
🟢 Sprint 6 In Progress

---

# 3. Current Sprint Goal

Xây dựng AI Pipeline trên resource đã upload: trích xuất nội dung, chunking, embedding và chuẩn bị truy vấn vector/RAG.

Sprint 6 chưa được triển khai trong code hiện tại.

---

# 4. Completed

## Backend

- Backend foundation, config, database connection, FastAPI lifespan và Health API
- Authentication: register, OAuth2 password login, Argon2id password hashing và JWT Bearer
- Default admin được tạo khi app khởi động
- Department, Major, Subject CRUD; GET public, ghi dữ liệu admin-only
- Resource/Asset model, JSONB metadata và soft delete
- Public resource list/detail; personal resource list; moderation workflow
- Sprint 5 upload: PDF/DOCX validation và lưu Asset trong MinIO
- Seed script idempotent cho một department, major, hai subject và user test

## Infrastructure

- Docker Compose chạy PostgreSQL `pgvector/pgvector:pg16` và MinIO
- `init-db/01-enable-pgvector.sql` bật extension `vector` khi Postgres khởi tạo volume mới

---

# 5. Next Task

- AI Pipeline: text extraction, chunking, embedding và vector retrieval
- Notebook Workspace và RAG Chat theo roadmap

---

# 6. Technology Stack

## Backend

- FastAPI, SQLAlchemy 2.0, PostgreSQL/JSONB và pgvector
- MinIO Python SDK
- pwdlib (Argon2id), PyJWT, Pydantic Settings
- `python-multipart` cho multipart upload

## Frontend / AI (planned)

- React/Vite/Tailwind CSS
- LangChain/OpenAI API/Sentence Transformers cho AI pipeline

---

# 7. Current Project Structure

```text
knowledge-sharing-platform/
├── backend/
│   ├── app/
│   │   ├── api/                 # auth, health, departments, majors, subjects, resources
│   │   ├── core/                # config, database, security
│   │   ├── models/              # SQLAlchemy entities and enums
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # business logic, MinIO adapter, startup
│   │   ├── workers/             # package placeholder
│   │   ├── main.py
│   │   └── seed.py
│   ├── alembic/                 # Alembic scaffold; no migration versions currently
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
├── init-db/01-enable-pgvector.sql
├── tests/
├── docs/
├── docker-compose.yml
└── .env.example
```

## Codebase Snapshot (update cuối mỗi Sprint)

```text
backend/app/
├── core/
│   ├── config.py        — Settings: PostgreSQL, MinIO, upload limits/allowlist, JWT và default-admin config
│   ├── database.py      — engine, SessionLocal, get_db()
│   └── security.py      — Argon2id hash/verify; JWT create/decode (HS256, 24h mặc định)
├── models/
│   ├── enums.py         — UserRole(USER, PREMIUM_USER, ADMIN); ResourceType(DOCUMENT, VIDEO, AUDIO, LINK, AI_ARTIFACT);
│   │                       VisibilityEnum(PRIVATE, PENDING_REVIEW, PUBLIC); ResourceStatus(PROCESSING, READY, FAILED, DELETED)
│   ├── user.py          — User(id, email, full_name, password_hash?, google_id?, role, is_active, created_at, resources)
│   ├── department.py    — Department(id, name, majors, subjects)
│   ├── major.py         — Major(id, department_id, code, name, department, subjects); major_subject association table
│   ├── subject.py       — Subject(id, department_id, code, name, department, majors, resources)
│   └── resource.py      — Resource(id, owner_id, subject_id?, title, description?, resource_type, visibility, status, created_at,
│                           metadata_json, assets); Asset(id, resource_id, file_name, file_path, file_type, size)
├── schemas/             — auth, department, major, subject và resource request/response schemas; AssetBase/AssetResponse nested in ResourceResponse
├── services/
│   ├── auth_service.py, department_service.py, major_service.py, subject_service.py
│   ├── resource_service.py — public/personal reads, resource lifecycle, validation và upload asset
│   ├── storage_service.py  — MinIO client, ensure_bucket(), upload_object(), delete_object()
│   └── startup_service.py  — tạo default admin nếu chưa tồn tại
├── api/                 — health, auth, departments, majors, subjects, resources; được gộp tại api/__init__.py
├── main.py              — create_all() và initialize_system() trong lifespan
└── seed.py              — seed dữ liệu demo idempotent
```

---

# 8. Backend Architecture

```text
Client → FastAPI Router → Dependencies/Auth Guard → Service Layer
       → SQLAlchemy Models → PostgreSQL
       → storage_service → MinIO
```

Business logic nằm trong Service Layer; router chỉ bind request/dependency và trả response.

### Resource and visibility flow

- Tạo resource cần JWT. User thường không truyền `visibility` sẽ tạo resource `PRIVATE`.
- User thường cũng có thể truyền trực tiếp `visibility=PENDING_REVIEW` khi tạo để đóng góp thẳng vào hàng chờ duyệt; code chỉ chặn trường hợp user không phải admin truyền `visibility=PUBLIC` (403).
- Admin có thể tạo trực tiếp resource với `visibility=PUBLIC`.
- Chủ sở hữu hoặc admin upload asset và submit review. Submit chỉ hợp lệ từ `PRIVATE` sang `PENDING_REVIEW`.
- Admin approve resource `PENDING_REVIEW` sang `PUBLIC`; list/detail công khai chỉ thấy resource `PUBLIC` chưa `DELETED`.
- `GET /resources/me` trả toàn bộ resource chưa bị xóa của người dùng hiện tại, bất kể visibility.
- Cập nhật, soft delete và approve là admin-only theo router hiện tại.

### Current API endpoints

- `GET /health`
- `POST /auth/register`, `POST /auth/login` (OAuth2 form: `username`, `password`), `GET /auth/me`
- `GET /departments/`, `GET /departments/{department_id}`; admin: `POST /departments/`, `PUT /departments/{department_id}`, `DELETE /departments/{department_id}`
- `GET /majors/`, `GET /majors/{major_id}`; admin: `POST /majors/`, `PUT /majors/{major_id}`, `DELETE /majors/{major_id}`
- `GET /subjects/`, `GET /subjects/{subject_id}`; admin: `POST /subjects/`, `PUT /subjects/{subject_id}`, `DELETE /subjects/{subject_id}`
- `GET /resources/?subject_id=<required>&resource_type=&page=1&size=20` (public only); `GET /resources/{resource_id}` (public only)
- JWT: `GET /resources/me`, `POST /resources/`, `POST /resources/{resource_id}/assets`, `POST /resources/{resource_id}/submit-review`
- Admin: `POST /resources/{resource_id}/approve`, `PUT /resources/{resource_id}`, `DELETE /resources/{resource_id}`

### Upload and storage flow

1. `POST /resources/{resource_id}/assets` nhận multipart `file` qua backend proxy.
2. Service kiểm tra quyền, file không rỗng, giới hạn `MAX_FILE_SIZE_MB` (30 mặc định), tối đa `MAX_ASSETS_PER_RESOURCE` (5 mặc định), và allowlist `ALLOWED_UPLOAD_FILE_TYPES` (`PDF`, `DOCX`).
3. PDF phải có header `%PDF-`; DOCX phải là ZIP chứa `[Content_Types].xml` và `word/document.xml`.
4. Tên file được chuẩn hóa; object ghi vào MinIO bucket `resources` (mặc định) theo `resources/{resource_id}/{uuid}_{filename}`.
5. Sau khi upload thành công, hệ thống tạo Asset với `file_name`, `file_path`, `file_type`, `size`. Nếu commit DB lỗi, service cố gắng xóa object vừa upload.

---

# 9. Coding Principles

- Service Layer Architecture; Separation of Concerns; Clean Code; Single Responsibility Principle.
- Không query database, đặt business logic hoặc SQL trực tiếp trong Router.
- Không hardcode config; upload limits và MinIO configuration lấy từ `Settings`/environment.

---

# 10. Technology Decisions

- ORM: SQLAlchemy 2.0, không dùng SQLModel.
- Database: PostgreSQL; Resource metadata dùng JSONB. pgvector đã có dependency/infrastructure nhưng AI schema/pipeline chưa có.
- Storage: MinIO; backend proxy upload, chưa dùng presigned URL.
- Migration runtime hiện dùng `Base.metadata.create_all()`; Alembic scaffold có mặt nhưng chưa có migration version.
- Primary key: integer.
- API chưa versioned (`/api/v1` chưa có).
- JWT là single access token HS256, expiry mặc định 24 giờ; chưa có refresh token.

---

# 11. Non-functional Requirements & Constraints

## Upload

- Chỉ nhận PDF và DOCX được xác thực nội dung cơ bản, không chỉ dựa extension.
- Giới hạn mặc định 30 MB/file và 5 asset/resource, có thể cấu hình bằng environment.
- Chưa có virus scan, download endpoint hay presigned URL trong code hiện tại.

## Known Risks / Constraints

- Đồ án solo trong một học kỳ; ngân sách OpenAI API và GPU free-tier hạn chế.
- AI Pipeline/RAG chưa triển khai, nên không mô tả như tính năng đã có.

---

# 12. Roadmap

1. ✅ Backend Foundation
2. ✅ Authentication
3. ✅ Department + Major + Subject
4. ✅ Resource & Asset Management
5. ✅ Upload System & File Validation
6. 🟢 AI Pipeline
7. Notebook Workspace
8. RAG Chat
9. Testing
10. Deployment & Optimization

---

# 13. AI Features (Planned)

Document upload → text extraction → chunking → embedding → pgvector → retriever/LLM → notebook chat, citation, summary; flashcards và quiz là optional.

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

Current Sprint: Sprint 6 — AI Pipeline

Current Module: Chưa có AI module; nền tảng upload và moderation của Resource/Asset đã hoàn thành.

Next Module: Notebook Workspace sau AI Pipeline.

---

# 18. Notes

Ưu tiên cân bằng System Core và AI/RAG, nhưng không over-engineer vượt quá khả năng hoàn thành của đồ án cá nhân.

---

# 19. Idea Backlog / Future Considerations

- Virus scanning và presigned upload/download URL.
- AI artifact layer (summary, flashcards, mindmap) có thể được lưu thành metadata hoặc Asset mới khi pipeline đã có.
- Quản lý chi phí OpenAI: giới hạn token/request, cache và quota theo user/session.
