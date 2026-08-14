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

> Sprint 8 — Code Structure Refactor (chưa bắt đầu)

Overall Progress

58%

Status

✅ Sprint 5 Completed
✅ Sprint 6 Completed
✅ Sprint 7 Completed

---

# 3. Current Sprint Goal

Sprint 7 (FE Catch-up Features) đã hoàn thành: nối toàn bộ màn hình shell với API thật cho browse taxonomy, resource cá nhân, upload/submit-review, admin moderation và admin taxonomy CRUD.

**Định hướng mới (sau Sprint 7):** Trước khi chuyển sang AI Pipeline, hoàn thiện một "bản Studocu cơ bản" đầy đủ UI như sản phẩm thực tế — dọn cấu trúc code trước, sau đó polish UI/UX trên nền code đã sạch (tránh phải sửa lại cùng file 2 lần), rồi bổ sung các tính năng lõi còn thiếu (download, search). AI Pipeline (roadmap mục 8) lùi lại thành sprint sau khi 3 sprint này hoàn thành. Đi chậm nhưng chắc để hiểu sâu nền tảng hiện tại trước khi mở rộng.

Sprint kế tiếp: **Sprint 8 — Code Structure Refactor** (xem mục 12 và mục 19 để biết chi tiết hạng mục).

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
- **Sprint 7 (backend phát sinh khi fix FE):**
  - `GET /majors/?department_id=` — lọc major theo khoa (optional; không truyền thì trả toàn bộ)
  - `GET /subjects/?major_id=` — lọc subject theo ngành (optional; không truyền thì trả toàn bộ)
  - `GET /resources/me/{resource_id}` — owner lấy resource của mình theo ID (mọi visibility trừ DELETED)
  - `GET /resources/admin` — admin list resource (filter `visibility`, paginated)
  - Service: `get_owned_by_id`, filter trong `major_service.get_all` / `subject_service.get_all`

## Frontend

- **Sprint 6 — FE Foundation:** Vite/React/TS/Tailwind, routing, API client, AuthContext, layout/navigation, login/register, ProtectedRoute/AdminRoute
- **Sprint 7 — FE Catch-up Features:**
  - TanStack Query v5 + react-hot-toast + shared UI (`Spinner`, `ErrorMessage`, `PaginationBar`)
  - Browse công khai: `DepartmentsPage` → `DepartmentDetailPage` → `MajorDetailPage` → `SubjectDetailPage` → `ResourceDetailPage`; `TaxonomyView` trên Home
  - `/me/resources` — danh sách resource cá nhân (badge visibility, rejection reason)
  - Luồng đóng góp 2 bước: `ResourceCreatePage` (PRIVATE) → `ResourceUploadPage` (upload PDF/DOCX + submit-review)
  - Admin: `AdminModerationPage` (approve/reject/delete PENDING_REVIEW), `AdminTaxonomyPage` (CRUD khoa/ngành/môn)
  - Query key factory (`resources/queryKeys`, `taxonomy/queryKeys`), cache invalidation sau mutation
  - `GET /resources/me/{id}` cho upload page; upload timeout riêng 120s; `getApiErrorMessage` cho toast lỗi backend
  - Validate URL param (`parseRouteId`), admin nav link cho role ADMIN, đồng bộ tiếng Việt UI

## Infrastructure

- Docker Compose chạy PostgreSQL `pgvector/pgvector:pg16` và MinIO
- `init-db/01-enable-pgvector.sql` bật extension `vector` khi Postgres khởi tạo volume mới

---

# 5. Next Task

**Sprint 8 — Code Structure Refactor**

- Tách logic ra khỏi pages: đưa `useQuery`/`useMutation`/form state của `ResourceCreatePage`, `ResourceUploadPage`, `AdminModerationPage`, `AdminTaxonomyPage` xuống feature hooks
- Dùng nhất quán query key factory (`resourcesKeys.myList`/`myListPaginated`) thay vì gọi trực tiếp `.me()`
- Gộp logic parse lỗi Axios: `AuthForm` dùng chung `getApiErrorMessage` thay vì tự parse riêng
- Tạo component dùng chung `DepartmentMajorSubjectPicker` cho cascade chọn khoa/ngành/môn (thay vì lặp ở 3 nơi)
- Dọn barrel export `features/resources/index.ts`, quy tắc rõ feature-specific vs app-wide UI component
- Cơ chế đồng bộ upload limit config FE/BE (ít nhất là 1 constant duy nhất tham chiếu)

Xem roadmap mục 12 cho Sprint 9 (UI/UX Polish & Design Consistency) và Sprint 10 (Core Feature Completion) tiếp theo.

---

# 6. Technology Stack

## Backend

- FastAPI, SQLAlchemy 2.0, PostgreSQL/JSONB và pgvector
- MinIO Python SDK
- pwdlib (Argon2id), PyJWT, Pydantic Settings
- `python-multipart` cho multipart upload

## Frontend (implemented)

- React 19 + Vite 8 + TypeScript + Tailwind CSS v3
- React Router v7, Axios, react-hook-form
- TanStack Query v5, react-hot-toast

## AI (planned, chưa triển khai)

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
│   ├── public/
│   ├── src/
│   │   ├── api/                 # apiClient, getApiErrorMessage
│   │   ├── components/
│   │   │   ├── ui/              # Button, Input, Modal, Spinner, ErrorMessage, PaginationBar
│   │   │   ├── AdminNavLinks.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   └── AdminRoute.tsx
│   │   ├── features/
│   │   │   ├── auth/            # api, context/, components/AuthForm
│   │   │   ├── resources/     # api, config, queryKeys, components/PublicResourceCard
│   │   │   └── taxonomy/        # api, queryKeys, components/TaxonomyView
│   │   ├── layouts/             # PublicLayout, AppLayout, AdminLayout
│   │   ├── pages/               # page components (lắp ráp + query/mutation wiring)
│   │   ├── router/              # AppRouter.tsx
│   │   ├── utils/               # parseRouteId
│   │   ├── App.tsx, main.tsx, index.css
│   │   └── assets/
│   ├── package.json, vite.config.ts, tailwind.config.js, tsconfig.json, .env
├── init-db/01-enable-pgvector.sql
├── tests/
├── docs/
├── docker-compose.yml
└── .env.example
```

## Codebase Snapshot (update cuối Sprint 7)

```text
backend/app/
├── core/
│   ├── config.py        — Settings: PostgreSQL, MinIO, upload limits/allowlist, JWT, default-admin
│   ├── database.py      — engine, SessionLocal, get_db()
│   └── security.py      — Argon2id hash/verify; JWT create/decode (HS256, 24h mặc định)
├── models/
│   ├── enums.py         — UserRole; ResourceType; VisibilityEnum; ResourceStatus
│   ├── user.py, department.py, major.py, subject.py, resource.py
├── schemas/             — auth, department, major, subject, resource (+ Asset nested)
├── services/
│   ├── auth_service.py, department_service.py, major_service.py, subject_service.py
│   ├── resource_service.py — public/personal/admin reads, lifecycle, upload, get_owned_by_id
│   ├── storage_service.py, startup_service.py
├── api/                 — health, auth, departments, majors, subjects, resources
├── main.py, seed.py

frontend/src/ (chính)
├── api/apiClient.ts, getApiErrorMessage.ts
├── components/ui/     — Button, Input, Modal, Spinner, ErrorMessage, PaginationBar
├── components/        — AdminNavLinks, ProtectedRoute, AdminRoute
├── features/
│   ├── auth/          — api, AuthContext, AuthForm
│   ├── resources/     — api, config.ts, queryKeys, PublicResourceCard
│   └── taxonomy/      — api, queryKeys, TaxonomyView
├── layouts/           — PublicLayout, AppLayout, AdminLayout
├── pages/             — Home, Departments, DepartmentDetail, MajorDetail, SubjectDetail,
│                        ResourceDetail, Login, Register, MyResources, ResourceCreate,
│                        ResourceUpload, AdminModeration, AdminTaxonomy
├── router/AppRouter.tsx
└── utils/parseRouteId.ts
```

---

# 8. Backend Architecture

```text
Client → FastAPI Router → Dependencies/Auth Guard → Service Layer
       → SQLAlchemy Models → PostgreSQL
       → storage_service → MinIO
```

## Frontend Architecture (Sprint 6–7)

```text
Browser → React Router → Layouts (Public/App/Admin) + Route Guards
       → TanStack Query + Feature modules (auth, taxonomy, resources)
       → Axios apiClient → FastAPI backend
       → AuthContext/localStorage → JWT session
       → react-hot-toast cho mutation feedback
```

Business logic nằm trong Service Layer; router chỉ bind request/dependency và trả response.

### Resource and visibility flow

- Tạo resource cần JWT. User thường không truyền `visibility` sẽ tạo resource `PRIVATE`.
- User thường cũng có thể truyền trực tiếp `visibility=PENDING_REVIEW` khi tạo; code chỉ chặn user không phải admin truyền `visibility=PUBLIC` (403).
- Admin có thể tạo trực tiếp resource với `visibility=PUBLIC`.
- Chủ sở hữu hoặc admin upload asset và submit review. Submit chỉ hợp lệ từ `PRIVATE` sang `PENDING_REVIEW`.
- Admin approve resource `PENDING_REVIEW` sang `PUBLIC`; list/detail công khai chỉ thấy resource `PUBLIC` chưa `DELETED`.
- `GET /resources/me` trả paginated toàn bộ resource chưa bị xóa của user hiện tại, bất kể visibility.
- `GET /resources/me/{resource_id}` trả một resource thuộc owner (không áp dụng filter public-only).
- `GET /resources/{resource_id}` (public) chỉ trả resource `PUBLIC`.
- Cập nhật, soft delete, approve/reject admin list và approve là admin-only theo router hiện tại.

### Current API endpoints

- `GET /health`
- `POST /auth/register`, `POST /auth/login` (OAuth2 form: `username`, `password`), `GET /auth/me`
- `GET /departments/`, `GET /departments/{department_id}`; admin: `POST`, `PUT`, `DELETE /departments/{department_id}`
- `GET /majors/?department_id=` (optional), `GET /majors/{major_id}`; admin: `POST`, `PUT`, `DELETE /majors/{major_id}`
- `GET /subjects/?major_id=` (optional), `GET /subjects/{subject_id}`; admin: `POST`, `PUT`, `DELETE /subjects/{subject_id}`
- `GET /resources/?subject_id=<required>&resource_type=&page=&size=` (public only)
- `GET /resources/{resource_id}` (public only)
- JWT: `GET /resources/me`, `GET /resources/me/{resource_id}`, `POST /resources/`, `POST /resources/{resource_id}/assets`, `POST /resources/{resource_id}/submit-review`
- Admin: `GET /resources/admin?visibility=&page=&size=`, `POST /resources/{resource_id}/approve`, `POST /resources/{resource_id}/reject`, `PUT /resources/{resource_id}`, `DELETE /resources/{resource_id}`

### Frontend routes (Sprint 7)

- Public: `/`, `/login`, `/register`, `/departments`, `/departments/:id`, `/majors/:id`, `/subjects/:id`, `/resources/:id`
- Protected: `/me/resources`, `/resources/create`, `/resources/:id/upload`
- Admin: `/admin/moderation`, `/admin/taxonomy`

### Upload and storage flow

1. `POST /resources/{resource_id}/assets` nhận multipart `file` qua backend proxy.
2. Service kiểm tra quyền, file không rỗng, giới hạn `MAX_FILE_SIZE_MB` (30 mặc định), tối đa `MAX_ASSETS_PER_RESOURCE` (5 mặc định), và allowlist `ALLOWED_UPLOAD_FILE_TYPES` (`PDF`, `DOCX`).
3. PDF phải có header `%PDF-`; DOCX phải là ZIP chứa `[Content_Types].xml` và `word/document.xml`.
4. Tên file được chuẩn hóa; object ghi vào MinIO bucket `resources` (mặc định) theo `resources/{resource_id}/{uuid}_{filename}`.
5. Sau khi upload thành công, hệ thống tạo Asset. Nếu commit DB lỗi, service cố gắng xóa object vừa upload.

---

# 9. Coding Principles

- Service Layer Architecture; Separation of Concerns; Clean Code; Single Responsibility Principle.
- Không query database, đặt business logic hoặc SQL trực tiếp trong Router.
- Không hardcode config; upload limits và MinIO configuration lấy từ `Settings`/environment.
- Frontend: feature modules (`features/{auth,taxonomy,resources}`) + pages lắp ráp; TanStack Query cho server state; query key factory cho cache invalidation.

---

# 10. Technology Decisions

- ORM: SQLAlchemy 2.0, không dùng SQLModel.
- Database: PostgreSQL; Resource metadata dùng JSONB. pgvector đã có dependency/infrastructure nhưng AI schema/pipeline chưa có.
- Storage: MinIO; backend proxy upload, chưa dùng presigned URL.
- Migration runtime hiện dùng `Base.metadata.create_all()`; Alembic scaffold có mặt nhưng chưa có migration version.
- Primary key: integer.
- API chưa versioned (`/api/v1` chưa có).
- JWT là single access token HS256, expiry mặc định 24 giờ; chưa có refresh token.
- FE upload limit mirror: `frontend/src/features/resources/config.ts` (phải khớp tay với `Settings.MAX_FILE_SIZE_MB` / `MAX_ASSETS_PER_RESOURCE`).

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
4. ✅ Resource (DB Refactor & CRUD)
5. ✅ Upload System & Visibility Workflow
6. ✅ FE Foundation
7. ✅ FE Catch-up Features
8. **Code Structure Refactor** (chưa bắt đầu) — dọn các quan sát cấu trúc code ở mục 19: tách logic khỏi pages xuống feature hooks, dùng nhất quán query key factory, gộp error handling, tạo `DepartmentMajorSubjectPicker` dùng chung, dọn barrel export, đồng bộ upload limit config FE/BE
9. **UI/UX Polish & Design Consistency** (chưa bắt đầu) — dọn các quan sát UI/UX ở mục 19 trên nền code đã sạch: entry point browse, Việt hóa badge, đồng bộ layout card/form component, responsive nav, gộp admin nav link, polish AdminTaxonomyPage
10. **Core Feature Completion** (chưa bắt đầu) — hoàn thiện tính năng lõi còn thiếu để giống sản phẩm thật: download endpoint, presigned URL (nếu còn thời gian), search cơ bản, rà lại toàn bộ luồng end-to-end
11. AI Pipeline (chưa bắt đầu — lùi lại sau khi Sprint 8-10 hoàn thành)
12. Notebook Workspace
13. RAG Chat
14. Testing
15. Deployment & Optimization

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

Current Sprint: Chưa bắt đầu — Sprint kế tiếp là **Sprint 8 — Code Structure Refactor**

Last Completed: Sprint 7 — FE Catch-up Features (browse flow, personal resources, upload/submit-review, admin moderation, admin taxonomy; backend filter endpoints và `GET /resources/me/{id}`)

Current Module: Toàn bộ luồng core FE–BE cho taxonomy browse, resource lifecycle và moderation đã nối API và hoạt động end-to-end.

Next Module: Sprint 8 (Code Structure Refactor) → Sprint 9 (UI/UX Polish) → Sprint 10 (Core Feature Completion) → sau đó mới tới AI Pipeline (roadmap mục 11). Mục tiêu: hoàn thiện một "bản Studocu cơ bản" đầy đủ UI như sản phẩm thực tế trước khi mở rộng AI, đi chậm nhưng chắc để hiểu sâu nền tảng hiện tại.

---

# 18. Notes

Ưu tiên cân bằng System Core và AI/RAG, nhưng không over-engineer vượt quá khả năng hoàn thành của đồ án cá nhân.

---

# 19. Idea Backlog / Future Considerations

## Backlog kỹ thuật (đã có từ trước)

- Virus scanning và presigned upload/download URL.
- AI artifact layer (summary, flashcards, mindmap) có thể được lưu thành metadata hoặc Asset mới khi pipeline đã có.
- Quản lý chi phí OpenAI: giới hạn token/request, cache và quota theo user/session.

## Quan sát UI/UX & cấu trúc code (đã đưa vào kế hoạch từ Sprint 8)

> Các mục dưới đây được ghi nhận khách quan từ code hiện tại sau Sprint 7. Đã được phân bổ vào Sprint 8 (cấu trúc code) và Sprint 9 (UI/UX) — xem mục 5 và mục 12.

### Layout / spacing / thẩm mỹ / nhất quán

- **HomePage:** Có hai lối browse song song — `TaxonomyView` (widget 3 bước) và khối "Bắt đầu nhanh" + nav "Duyệt theo khoa" dẫn tới `/departments`; trải nghiệm trùng lặp, chưa thống nhất một entry point duy nhất.
- **PublicLayout:** Thanh nav gom nhiều link (browse, trang chủ, tài liệu, đóng góp, admin, user) trên một hàng — dễ chật trên viewport hẹp, chưa có responsive collapse/menu.
- **Browse pages (`DepartmentsPage`, `DepartmentDetailPage`, `MajorDetailPage`, `SubjectDetailPage`):** Cùng pattern `max-w-5xl px-6 py-12` nhưng link "Quay lại" không nhất quán (một số về `/`, một số về `/departments`, `MajorDetailPage` về khoa cha).
- **ResourceDetailPage:** Badge hiển thị raw enum tiếng Anh (`resource_type`, `status` — ví dụ `DOCUMENT`, `READY`) trong khi các trang khác đã Việt hóa label.
- **ResourceUploadPage:** Badge visibility vẫn hiển thị raw enum (`PRIVATE`, `PENDING_REVIEW`) thay vì label tiếng Việt như `MyResourcesPage`.
- **MyResourcesPage vs SubjectDetailPage:** Card resource khác layout hoàn toàn — grid 2 cột có badge/reject/upload (cá nhân) vs list link đơn giản (công khai qua `PublicResourceCard`); hợp lý về nghiệp vụ nhưng chưa có design system thống nhất.
- **ResourceCreatePage:** Form dùng raw `<input>`/`<select>` Tailwind inline; **Login/Register** dùng shared `Input`/`Button` — không đồng nhất component form.
- **AdminModerationPage / AdminTaxonomyPage:** Nội dung admin nằm trong card trắng giống AppLayout pages, nhưng markup JSX bị nén một dòng ở bảng/modal (`AdminTaxonomyPage`) — khó đọc và khó chỉnh spacing từng cell.
- **AdminTaxonomyPage:** Bảng HTML thuần không có zebra/hover rõ, modal form dày đặc, thiếu empty-state illustration nhất quán với trang public.
- **AppLayout vs PublicLayout:** Link admin xuất hiện ở cả nav ngang (`AdminNavLinks`) và sidebar AppLayout — admin thấy hai cách vào cùng chức năng tùy layout đang ở.

### Cấu trúc code frontend (lệch convention / trùng lặp)

- **`pages/` chứa logic nghiệp vụ:** Doc convention ghi "pages chỉ lắp ráp", nhưng `ResourceCreatePage`, `ResourceUploadPage`, `AdminModerationPage`, `AdminTaxonomyPage` chứa trực tiếp `useQuery`/`useMutation`, form state, invalidate cache — logic chưa tách xuống feature hooks/components.
- **`AdminNavLinks` vs `AppLayout` sidebar:** Link admin được định nghĩa ở hai nơi (`components/AdminNavLinks.tsx` và inline trong `AppLayout.tsx`) — trùng lặp, dễ lệch khi đổi route/label.
- **Error handling API:** `getApiErrorMessage.ts` dùng cho toast mutation, nhưng `AuthForm.tsx` vẫn parse lỗi Axios riêng với nhánh status 401/409 — hai pattern song song.
- **Query key factory:** `resourcesKeys` định nghĩa `myList`/`myListPaginated` nhưng `MyResourcesPage` và `ResourceUploadPage` dùng `resourcesKeys.me()` trực tiếp — factory chưa được dùng nhất quán.
- **Vị trí shared component:** `PublicResourceCard` nằm `features/resources/components/`; `PaginationBar` nằm `components/ui/` — chưa có quy tắc rõ feature-specific vs app-wide UI.
- **Cascade taxonomy chọn khoa/ngành/môn:** Logic tương tự lặp giữa `TaxonomyView`, `ResourceCreatePage`, và phần editor Subject trong `AdminTaxonomyPage` — chưa có hook/component dùng chung (ví dụ `DepartmentMajorSubjectPicker`).
- **`features/resources/index.ts`:** Barrel chỉ re-export `api` — component `PublicResourceCard` import trực tiếp từ path sâu, barrel gần như không dùng.
- **Upload config mirror:** `features/resources/config.ts` hardcode 30MB/5 assets — cần sync tay với backend env (đã comment trong file nhưng chưa có cơ chế single source of truth).