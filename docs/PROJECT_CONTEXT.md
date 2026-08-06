# PROJECT_CONTEXT.md

# Knowledge Sharing Platform

> Graduation Project - AI-powered Knowledge Sharing Platform inspired by Studocu + NotebookLM

---

# 1. Project Overview

## Description

Knowledge Sharing Platform là hệ thống chia sẻ tài liệu học tập kết hợp AI, lấy cảm hứng từ Studocu và NotebookLM.

Mục tiêu của đồ án không phải clone Studocu mà xây dựng một nền tảng cho phép:

- Chia sẻ tài liệu học tập
- Quản lý tài liệu theo Khoa → Ngành → Môn học (kiến trúc thiết kế để có thể mở rộng nhiều Khoa/Ngành, nhưng demo sẽ scope trong 1 Ngành để tập trung đầu tư cho RAG Pipeline — chi tiết cụ thể chưa chốt hẳn, sẽ rõ hơn khi làm đến Frontend)
- Upload PDF, DOCX,...
- AI đọc tài liệu
- AI trả lời câu hỏi dựa trên tài liệu
- Notebook cá nhân
- Personal Knowledge Base
- Public Knowledge Hub

---

# 2. Current Progress

Current Sprint

> Sprint 4 — Learning Resource CRUD

Overall Progress

35%

Status

🟢 Sprint 3 Completed

---

# 3. Current Sprint Goal

Xây dựng CRUD cho Learning Resource trước khi phát triển Upload System.

Mục tiêu Sprint 4:

- Learning Resource CRUD (list, create, update, delete — Admin only)
- Public read endpoints cho Learning Resource nếu cần theo scope Sprint 4

---

# 4. Completed

## Backend

- Project Structure
- SQLAlchemy Models
- Database Connection
- Config Management
- FastAPI Main
- Health API
- Authentication (Register, Login, Password Hashing, JWT) — Sprint 2 ✅
- System Initialization / Default Admin Seed
- Department CRUD — Sprint 3 ✅
- Major CRUD — Sprint 3 ✅
- Subject CRUD — Sprint 3 ✅

## Infrastructure

- Docker Compose
- PostgreSQL
- MinIO

## Database Models

- User
- Department
- Major
- Subject
- LearningResource

---

# 5. Next Task

Sau Learning Resource CRUD (Sprint 4) sẽ tiếp tục:

- Upload System (Sprint 5)
- AI Pipeline (Sprint 6)

---

# 6. Technology Stack

## Backend

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- pgvector
- MinIO
- pwdlib (Argon2id) — password hashing
- PyJWT — access token

## Frontend

- React
- Vite
- Tailwind CSS

## AI

- LangChain
- OpenAI API
- Sentence Transformers
- pgvector

---

# 7. Current Project Structure

```
knowledge-sharing-platform/

backend/
frontend/
docs/

README.md
```

Backend

```
app/

api/
core/
models/
schemas/
services/

main.py
```

## Codebase Snapshot (update cuối mỗi Sprint)

```text
app/
├── core/
│   ├── config.py        — class Settings(BaseSettings): APP_NAME, DEBUG, POSTGRES_*, MINIO_*,
│   │                       ADMIN_*, JWT_SECRET_KEY, JWT_ALGORITHM="HS256",
│   │                       JWT_EXPIRE_MINUTES=1440 (24h), DATABASE_URL @property; settings = Settings()
│   ├── database.py      — engine, SessionLocal, get_db() -> Generator[Session, None, None]
│   └── security.py      — hash_password(), verify_password() [pwdlib Argon2id],
│                           create_access_token(subject, role), decode_access_token(token) [PyJWT]
├── models/
│   ├── base.py          — class Base(DeclarativeBase)
│   ├── enums.py         — UserRole(STUDENT, ADMIN), ResourceType, VisibilityEnum, ResourceStatus
│   ├── user.py          — class User(id, email, full_name, password_hash, google_id, role,
│   │                       is_active, created_at, resources)
│   ├── department.py    — class Department(id, name, majors, subjects)
│   ├── major.py         — class Major(id, department_id, code, name, department, subjects),
│   │                       major_subject table
│   ├── subject.py       — class Subject(id, department_id, code, name, department, majors, resources)
│   ├── learning_resource.py
│   │                    — class LearningResource(id, owner_id, subject_id, title, description,
│   │                       file_type, visibility, status, file_path, created_at, owner, subject)
│   └── __init__.py      — exports: Base, User, Department, Major, Subject, LearningResource
├── schemas/
│   ├── auth.py          — RegisterRequest, LoginRequest, UserResponse, TokenResponse
│   ├── department.py    — DepartmentBase, DepartmentCreate, DepartmentUpdate, DepartmentResponse
│   ├── major.py         — MajorBase, MajorCreate, MajorUpdate, MajorResponse
│   ├── subject.py       — SubjectBase, SubjectCreate, SubjectUpdate, SubjectResponse
│   └── __init__.py      — (hiện tại file trống)
├── services/
│   ├── auth_service.py  — register_user(db, data), authenticate_user(db, email, password),
│   │                       get_user_from_token(db, token), create_user_token(user)
│   ├── startup_service.py — initialize_system(db), ensure_admin_exists(db)
│   ├── department_service.py — get_all/get_by_id/create/update/delete for Department
│   ├── major_service.py  — get_all/get_by_id/create/update/delete for Major
│   ├── subject_service.py — get_all/get_by_id/create/update/delete for Subject,
│   │                       validates department_id and major_ids in service layer
│   └── __init__.py      — (hiện tại file trống)
├── api/
│   ├── health.py        — router = APIRouter(prefix="/health"), GET /health -> health_check()
│   ├── auth.py          — router = APIRouter(prefix="/auth"), OAuth2PasswordBearer,
│   │                       get_current_user(), get_current_admin(), POST /auth/register,
│   │                       POST /auth/login, GET /auth/me
│   ├── departments.py   — public GETs, admin-only POST/PUT/DELETE
│   ├── majors.py        — public GETs, admin-only POST/PUT/DELETE
│   ├── subjects.py      — public GETs, admin-only POST/PUT/DELETE
│   └── __init__.py      — api_router = APIRouter(), include_router(health/auth/departments/majors/subjects)
└── main.py               — lifespan(app), Base.metadata.create_all(bind=engine), initialize_system(db),
                             app = FastAPI(title=settings.APP_NAME, lifespan=lifespan),
                             include_router(api_router)
```

---

# 8. Backend Architecture

```
Client

↓

FastAPI

↓

API Router

↓

Service Layer

↓

SQLAlchemy Models

↓

PostgreSQL

↓

MinIO (Storage)
```

Business Logic luôn nằm trong Service Layer.

Router chỉ nhận Request và trả Response.

---

# 9. Coding Principles

Luôn tuân theo các nguyên tắc sau.

## Architecture

- Service Layer Architecture
- Separation of Concerns
- Clean Code
- Single Responsibility Principle

## Không được

❌ Query Database trong Router

❌ Business Logic trong Router

❌ SQL trong API

❌ Code trùng lặp

❌ Hardcode Config

---

# 10. Technology Decisions

Đã thống nhất:

## ORM

SQLAlchemy 2.0

Không sử dụng SQLModel.

---

## Database

PostgreSQL

---

## Vector Database

pgvector

Không dùng Pinecone.

---

## Object Storage

MinIO

---

## Migration

Hiện tại sử dụng

Base.metadata.create_all()

Alembic sẽ tích hợp sau nếu còn thời gian.

---

## Primary Key

Integer

Không dùng UUID.

---

## API Version

Chưa sử dụng

api/v1

Đợi khi project đủ lớn mới tách version.

---

## Password Hashing

pwdlib + Argon2id (PasswordHash.recommended())

Không dùng passlib/bcrypt.

Logic nằm trong `core/security.py`, được gọi từ `services/auth_service.py`, không nằm trong Router.

---

## Authentication

Single Access Token (JWT, thuật toán HS256), expiry 24h.

Chưa làm Refresh Token — lý do: đồ án solo 1 học kỳ, Refresh Token kéo theo storage/revoke/rotation/refresh endpoint/frontend interceptor, chưa có requirement đủ mạnh để justify complexity đó.

JWT payload gồm `sub` (user id) và `role`, để check quyền Admin sau này không cần query lại DB.

---

## Upload / Storage

React → FastAPI (Backend Proxy) → MinIO.

Chưa dùng Presigned URL ở Phase đầu (chỉ định hướng PDF/DOCX, chưa có requirement file cực lớn). Sẽ chuyển sang Presigned URL nếu sau này backend trở thành bottleneck.

Tách `Router → Service → StorageService → MinIO` để sau này đổi MinIO sang S3 hoặc storage khác được dễ hơn.

---

# 11. Non-functional Requirements & Constraints

## Upload

- Giới hạn dung lượng file: (chưa chốt cụ thể, cần quyết định trước Sprint 5)
- Định dạng cho phép: PDF, DOCX

## Authentication

- JWT: Single Access Token, HS256, expiry 24h. Đã chốt ở Sprint 2 (xem mục 10).

## API Cost Management (OpenAI API)

- Cần có cơ chế giới hạn/quản lý chi phí khi gọi OpenAI API vì dùng ví cá nhân, ví dụ: giới hạn token mỗi request, cache câu trả lời cho câu hỏi lặp lại, giới hạn số lượt gọi API theo user/session.
- Chi tiết cơ chế cụ thể sẽ quyết định khi triển khai Sprint 6 (AI Pipeline).

## Known Risks / Constraints

- Đồ án cá nhân, thực hiện solo trong 1 học kỳ.
- Giới hạn tài nguyên GPU: chỉ dùng free-tier (Colab/Kaggle), không có GPU riêng.
- Ngân sách gọi OpenAI API là cá nhân, cần cân nhắc chi phí khi thiết kế AI Pipeline.
- Mọi đề xuất kỹ thuật cần tính đến các giới hạn trên, tránh đề xuất giải pháp vượt quá khả năng thực hiện của 1 sinh viên trong 1 học kỳ.

---

# 12. Roadmap

Sprint 1

✅ Backend Foundation

↓

Sprint 2

✅ Authentication

↓

Sprint 3

🟢 Department + Subject (đang làm)

↓

Sprint 4

Learning Resource

↓

Sprint 5

Upload System

↓

Sprint 6

AI Pipeline

↓

Sprint 7

Notebook Workspace

↓

Sprint 8

RAG Chat

↓

Sprint 9

Testing

↓

Sprint 10

Deployment & Optimization

---

# 13. AI Features (Planned)

Document Upload

↓

Chunking

↓

Embedding

↓

pgvector

↓

Retriever

↓

LLM

↓

Notebook Chat

↓

Citation

↓

Summary

↓

Flashcards (Optional)

↓

Quiz Generation (Optional)

---

# 14. Development Workflow

Mỗi Sprint sẽ theo quy trình:

Planning

↓

Implementation

↓

Testing

↓

Documentation

↓

Commit

↓

Push GitHub

---

# 15. Git Convention

Commit theo Sprint hoặc Feature.

Ví dụ:

feat: initialize backend foundation

feat: implement authentication

feat: add upload module

feat: integrate rag pipeline

Không commit kiểu:

update

fix

abc

123

---

# 16. AI Collaboration Instructions

Nếu AI đọc file này, hãy:

- Hiểu toàn bộ bối cảnh project trước khi trả lời.
- Không đề xuất thay đổi kiến trúc nếu không thật sự cần.
- Ưu tiên giữ code đơn giản, dễ hiểu và phù hợp với đồ án đại học.
- Giải thích ngắn gọn nhưng đúng bản chất.
- Hướng dẫn theo từng Sprint, không nhảy quá xa.
- Khi đề xuất cấu trúc hoặc thư viện mới, giải thích lý do sử dụng.
- Luôn ưu tiên tính ổn định và khả năng hoàn thành đồ án đúng tiến độ.
- Đầu tư thời gian và độ kỹ lưỡng ngang nhau giữa System Core (Backend, Database, Kiến trúc) và AI Pipeline (RAG, Notebook) — không ưu tiên bên nào hơn bên nào.
- Cân nhắc các giới hạn tài nguyên (free-tier GPU, ngân sách API cá nhân, thời gian 1 học kỳ solo) khi đề xuất giải pháp.

---

# 17. Current Status

Current Sprint

Sprint 3

Current Module

Department + Subject

Next Module

Learning Resource

Current Focus

Xây dựng CRUD cho Department và Subject (Admin quản lý, public read), làm nền cho Learning Resource CRUD ở Sprint 4.

---

# 18. Notes

Đây là đồ án cá nhân.

Mục tiêu lớn nhất không phải sử dụng thật nhiều công nghệ, mà là:

- Xây dựng một hệ thống hoàn chỉnh, cả phần System Core (Backend, Database, Kiến trúc) lẫn phần AI (RAG, Notebook, pgvector) đều được đầu tư kỹ lưỡng và ngang mức độ ưu tiên với nhau — không thiên lệch bên nào.
- Hiểu rõ kiến trúc của từng thành phần, từ hạ tầng backend đến pipeline AI.
- Có khả năng giải thích mọi quyết định thiết kế khi bảo vệ đồ án, cả về System Design lẫn về AI.
- Tránh sa đà vào hạ tầng không cần thiết (over-engineering), nhưng cũng không được xem nhẹ chất lượng và độ vững chắc của System Core để dồn hết thời gian cho AI.

Mọi đề xuất nên cân bằng giữa tính thực tế, độ phức tạp và thời gian hoàn thành của một sinh viên thực hiện trong một học kỳ, đồng thời giữ mức đầu tư ngang nhau giữa System Core và AI Pipeline.