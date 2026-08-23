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
Hệ thống đang chuyển đổi triệt để sang mô hình sprint "vertical slice" (triển khai hoàn chỉnh cả Frontend + Backend trong cùng một sprint thay vì tách rời lẻ tẻ). Sprint 10 là sprint dọc đầu tiên hoàn thành giao diện & API Dashboard cơ bản (tạo mới + danh sách), chuẩn bị bước vào Sprint 10.5 để hoàn tất đổi tên / xóa.

Current Sprint

> Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload

Overall Progress

85%

Status

✅ Sprint 5 Completed
✅ Sprint 6 Completed
✅ Sprint 7 Completed
✅ Sprint 8 Completed
✅ Sprint 8.5 — Database Architecture Refactor — **hoàn thành**
✅ Sprint 9 — UI/UX Polish & Design Consistency — **hoàn thành**
✅ Sprint 10 — Notebook (AI Workspace) Feature — Dashboard + Layout Redesign — **hoàn thành**
✅ Sprint 10.5 — Notebook Dashboard Actions (Rename/Delete) — **hoàn thành**
🔄 Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload — **đang thực hiện**

---

# 3. Current Sprint Goal

Sprint 9 (UI/UX Polish & Design Consistency) đã hoàn thành: chuẩn hóa UI/UX, áp dụng luồng Progressive Disclosure, tích hợp tìm kiếm môn học tức thì không dấu và PDF preview modal, tối giản hóa Flat Document List, đổi tên và cấu trúc thư mục sang `documents`.

**Sprint 10 — Notebook (AI Workspace) Feature — Dashboard + Layout Redesign:** Thiết kế và hoàn thiện toàn bộ giao diện dashboard, cấu trúc thư mục `features/notebooks` bám sát `features/documents`, triển khai card, modal tạo mới, bộ lọc local client-side, dynamic welcome header, tối ưu service/API backend đếm tài liệu và tích hợp hệ thống layout Dark Sidebar thống nhất, ẩn `SubjectSearchInput` khi ở trang workspace.

**Sprint 10.5 — Notebook Dashboard Actions (Rename/Delete):** Triển khai các API và tương tác giao diện chỉnh sửa tên và xóa bỏ Notebook, giải quyết các vướng mắc về chính sách đồng bộ quản lý tài liệu. (Hoàn thành hoàn toàn cả API Backend và UI Frontend với Kebab menu + Modals).

**Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload:** Xây dựng trang chi tiết Notebook thật hỗ trợ cả FE + BE. Xây dựng backend + frontend cho phép lưu tài liệu công cộng (Document) vào Notebook cá nhân với giới hạn `MAX_SAVED_DOCUMENTS_PER_NOTEBOOK = 10`. Xây dựng tính năng upload tập tin cá nhân riêng vào Notebook với giới hạn `MAX_OWN_ASSETS_PER_NOTEBOOK = 5`.

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
  - Enums: `DocumentStatus` (DRAFT/PUBLIC/DELETED), `ResourceType` (EXAM/SLIDE/DOCUMENT/VIDEO/AUDIO/LINK/AI_ARTIFACT)
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
  - `npm run build` ✅ hoạt động ổn định không lỗi type/import.

## Infrastructure

- Docker Compose chạy PostgreSQL `pgvector/pgvector:pg16` và MinIO
- `init-db/01-enable-pgvector.sql` bật extension `vector` khi Postgres khởi tạo volume mới

---

# 5. Next Task

## Ngay lúc này: Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload

- **Màn hình chi tiết**: Xây dựng trang chi tiết Notebook thật hỗ trợ cả FE + BE. ⚠️ CHƯA CHỐT: thiết kế cấu trúc giao diện 1 cột hay 2 cột kiểu của NotebookLM.
- **Lưu tài liệu**: Xây dựng backend + frontend cho phép lưu tài liệu công cộng (Document) vào Notebook cá nhân với hạn định giới hạn `MAX_SAVED_DOCUMENTS_PER_NOTEBOOK = 10`.
- **Đóng góp cá nhân**: Xây dựng tính năng upload tập tin cá nhân riêng vào Notebook với hạn định giới hạn `MAX_OWN_ASSETS_PER_NOTEBOOK = 5`.

## Sprint 12+ (Dời lại): AI Features (RAG Chat, embeddings, chunking)

- Phát triển pipeline chunking/embedding, lưu trữ pgvector và kết nối LLM để hỗ trợ chat, trích dẫn tài liệu trong Notebook.

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

> Cập nhật sau Sprint 10. Model `Resource` cũ đã xóa hoàn toàn.

```text
knowledge-sharing-platform/
├── backend/
│   ├── app/
│   │   ├── api/       # health, auth, config, departments, majors, subjects, documents, notebooks
│   │   ├── core/      # config, database, security
│   │   ├── models/    # base, enums, user, department, major, subject,
│   │   │              # document, notebook, asset
│   │   ├── schemas/   # auth, department, major, subject, document, asset, notebook
│   │   ├── services/  # auth, department, major, subject, document, asset,
│   │   │              # storage, startup, notebook_service
│   │   ├── main.py, seed.py
│   ├── alembic/
│   ├── Dockerfile, requirements.txt, .env.example
├── frontend/src/
│   ├── api/           # apiClient, getApiErrorMessage
│   ├── components/ui/ # Button, Input, Modal, Spinner, ErrorMessage, PaginationBar
│   ├── components/    # AdminNavLinks, ProtectedRoute, AdminRoute
│   ├── features/
│   │   ├── auth/      # api, AuthContext, AuthForm
│   │   ├── documents/ # api (Document types), queryKeys (documentsKeys),
│   │   │              # hooks/ (useDocuments, useDocumentDetail, useUploadConfig),
│   │   │              # components/PublicResourceCard, index.ts
│   │   ├── notebooks/ # api, queryKeys, hooks/useNotebooks, hooks/useCreateNotebook,
│   │   │              # components/NotebookCard, components/CreateNotebookCard, components/CreateNotebookModal
│   │   ├── taxonomy/  # api, queryKeys, TaxonomyView, DepartmentMajorSubjectPicker, hooks/
│   │   └── README.md
│   ├── layouts/       # PublicLayout, AppLayout, AdminLayout
│   ├── pages/         # active: Home, Departments, DepartmentDetail, MajorDetail,
│   │                  #         SubjectDetail, DocumentDetail, Login, Register,
│   │                  #         MyNotebooksPage, NotebookDetailPage,
│   │                  #         MyResources (notice), AdminTaxonomy
│   │                  # stubbed: ResourceCreate, ResourceUpload, AdminModeration
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

### Current API endpoints (Sprint 10)

- `GET /health`
- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `GET /departments/`, `GET /departments/{id}`; admin: `POST`, `PUT`, `DELETE`
- `GET /majors/?department_id=`, `GET /majors/{id}`; admin: `POST`, `PUT`, `DELETE`
- `GET /subjects/?major_id=`, `GET /subjects/{id}`; admin: `POST`, `PUT`, `DELETE`
- `GET /documents/?subject_id=&resource_type=&page=&size=` (only PUBLIC)
- `GET /documents/{id}` (only PUBLIC, nested assets)
- `GET /documents/{id}/assets/{asset_id}/download` → presigned MinIO URL (no JWT)
- `GET /config/upload`
- `POST /notebooks/` (JWT protected)
- `GET /notebooks/me` (JWT protected)
- `PATCH /notebooks/{notebook_id}` (JWT protected)
- `DELETE /notebooks/{notebook_id}` (JWT protected)

### Frontend routes (Sprint 10)

- Public (active): `/`, `/login`, `/register`, `/departments`, `/departments/:id`, `/majors/:id`, `/subjects/:id`, `/resources/:id`, `/documents/:id`
- Protected (active): `/me/workspace` (MyNotebooksPage), `/me/workspace/:notebookId` (NotebookDetailPage - placeholder), `/me/resources` (temp notice)
- Admin (active): `/admin/taxonomy`
- Commented out: `/resources/create`, `/resources/:id/upload`, `/admin/moderation`

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
- Centralized configurations: Upload limit configurations được quản lý tập trung ở settings backend và cung cấp cho frontend qua API GET `/config/upload` để đảm bảo duy nhất nguồn dữ liệu (single source of truth).
- Action-Based Hooks Pattern: Toàn bộ data fetching và state mutation được đóng gói thành các custom hook riêng trong feature layer (ví dụ: client-side CRUD và actions), giúp pages chỉ làm nhiệm vụ lắp ghép giao diện (UI layout composition).

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
8. ✅ Code Structure Refactor
8.5. ✅ **Database Architecture Refactor** — **hoàn thành**
9. ✅ **UI/UX Polish & Design Consistency** — **hoàn thành**
10. ✅ **Notebook (AI Workspace) Feature — Dashboard + Layout Redesign** — **hoàn thành**
10.5. ✅ **Notebook Dashboard Actions (Rename/Delete)** — **hoàn thành**
11. 🔄 **Notebook Detail Page & Document Saving / Asset Upload** — **đang thực hiện**
12. 🔄 **AI Features (RAG Chat, embeddings, chunking)** — **dời lại**
13. 🔄 **Testing & Deployment** — **kế hoạch**
14. 🔄 **Deployment & Optimization** — **kế hoạch**

---

# 13. AI Features (Planned)

Document upload → text extraction → chunking → embedding → pgvector → retriever/LLM → notebook chat, citation, summary; flashcards và quiz là optional.

*(Đề xuất sơ bộ về bảng embedding — `AssetEmbedding`, gắn theo `asset_id` để tránh embed trùng file Public được nhiều Notebook lưu — xem mục 19c. Đây mới là ý tưởng logic, chưa có thiết kế kỹ thuật chi tiết về chunking/dimension/index.)*

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

Current Status: **Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload** (đang thực hiện)

Last Completed: Sprint 10.5 — Notebook Dashboard Actions (Rename/Delete) (hoàn thành các API Backend cập nhật tên/xóa notebook đi kèm background worker dọn dẹp MinIO, các UI component Kebab menu dropdown ngăn nổi bọt sự kiện, modal đổi tên và xác nhận xóa, nâng hạn mức 500 ký tự).

Next Module: Sprint 11 (Notebook Detail Page & Document Saving / Asset Upload) → Sprint 12 (AI Features / RAG Chat).

---

# 18. Notes

Ưu tiên cân bằng System Core và AI/RAG, nhưng không over-engineer vượt quá khả năng hoàn thành của đồ án cá nhân.

---

# 19. Idea Backlog / Future Considerations

## 19a. Backlog kỹ thuật (đã có từ trước)

- Virus scanning và presigned upload/download URL.
- AI artifact layer (summary, flashcards, mindmap) có thể được lưu thành metadata hoặc Asset mới khi pipeline đã có.
- Quản lý chi phí OpenAI: giới hạn token/request, cache và quota theo user/session.

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

**Quota Notebook** (tách 2 config thay vì gộp 1)
- `MAX_OWN_ASSETS_PER_NOTEBOOK` = 5 (mặc định) — đếm file user tự upload trực tiếp (tốn storage + phải embed mới).
- `MAX_SAVED_DOCUMENTS_PER_NOTEBOOK` = 10 (đã chốt) — đếm Document lưu qua liên kết logic (không tốn embed lại, chỉ tốn context lúc query). Để dạng config, không hard-code, dễ điều chỉnh sau khi thấy chi phí context RAG thực tế.
- Lý do tách: nếu gộp chung, lưu 5 tài liệu Public là hết quota, không upload riêng được nữa — không hợp lý vì bản chất chi phí khác nhau.

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