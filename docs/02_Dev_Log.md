# Sprint 1.2

## Goal

Backend Foundation

---

## Completed

- Config
- Database
- Main
- Health API

---

## Decisions

- SQLAlchemy thay SQLModel
- Chưa dùng Alembic

---

## Learned

- FastAPI Lifespan
- Dependency Injection
- SQLAlchemy Session

---

## Next Sprint

Authentication

---

# Sprint 2

## Goal

Authentication

---

## Completed

- Register
- Login
- Password Hashing
- JWT Authentication

---

## Decisions

- pwdlib (Argon2id) cho password hashing
- PyJWT cho access token
- Auth tách theo Service Layer

---

## Learned

- OAuth2PasswordBearer cho Bearer token flow
- JWT payload nên mang `sub` và `role`
- Service layer giữ business logic cho auth

---

## Next Sprint

Department + Major + Subject CRUD

---

# Sprint 3

## Goal

Department + Major + Subject CRUD

## Completed

- Department CRUD
- Major CRUD
- Subject CRUD
- Public read endpoints for Department/Major/Subject
- Admin-only write guard via dependency

## Decisions

- Router -> Service -> Model architecture for academic CRUD
- SQLAlchemy 2.0 `Session.execute(select(...))` for service queries
- Subject create/update resolves `major_ids` in service layer
- Department delete is restricted when related majors or subjects exist

## Learned

- Keep authorization in dependencies to keep routers thin
- Validate foreign keys in the service layer before mutating models
- Use lightweight nested response schemas to avoid circular imports

## Next Sprint

Resource & Asset Management

---

# Sprint 4

## Goal

Resource & Asset Management

## Completed

- Resource / Asset model split
- JSONB metadata-first schema
- ResourceType taxonomy update
- User.resources and Subject.resources rewired to Resource
- Resource update/delete API for admin writes (Sprint 5 later mở create/upload/submit cho JWT user)
- Public read endpoints with pagination and subject filtering
- Soft delete via ResourceStatus.DELETED

## Decisions

- Resource is the metadata-first entity; Asset is the physical file layer
- JSONB is used for extensible metadata instead of new static columns
- Business logic remains in Service Layer; resource router now mirrors the Department/Major/Subject pattern

## Learned

- Model refactors should land before CRUD to reduce schema churn later
- Relationship rewiring must be updated together with exports to avoid stale imports
- Soft delete is the safer default for resource lifecycles because Sprint 6+ will attach embeddings and related derived data

## Next Sprint

Upload System & File Validation

---

# Sprint 5

## Goal

Upload System & Visibility Workflow

---

## Completed

- Upload PDF/DOCX asset qua FastAPI vào MinIO
- `storage_service` adapter tạo bucket khi cần và ghi/xóa object
- Kiểm tra file rỗng, kích thước tối đa, số asset tối đa và allowlist cấu hình
- Xác thực chữ ký PDF; xác thực DOCX là ZIP có các entry bắt buộc
- Lưu `Asset` chỉ sau khi upload thành công; dọn object MinIO nếu commit DB lỗi
- Endpoint xem resource của chính chủ, submit review và admin approve
- Visibility workflow: `PRIVATE → PENDING_REVIEW → PUBLIC`

---

## Decisions

- Backend proxy upload thay vì presigned URL ở MVP.
- Chỉ hỗ trợ PDF và DOCX ở Sprint 5; các `ResourceType` khác vẫn là taxonomy dữ liệu.
- Chủ sở hữu hoặc admin có thể upload/submit; chỉ admin có thể approve hoặc cập nhật/xóa resource.

---

## Rationale

- Roadmap cũ gộp FE Foundation và FE Catch-up Features thành 1 sprint lớn, gây rủi ro về chất lượng và khó kiểm thử.
- Tách Sprint 6 (FE Foundation, hạ tầng + auth shell) và Sprint 7 (FE Catch-up Features, UI cho backend Sprint 1–5) để mỗi sprint có phạm vi rõ ràng.
- Sprint 8–10 áp dụng mô hình vertical slice cho AI Pipeline, Notebook Workspace và RAG Chat vì đây là tính năng user-facing mới cần backend và frontend đi cùng nhau để test toàn bộ luồng ngay trong sprint.

## Next Sprint

FE Foundation

---

# Sprint 6

## Goal

FE Foundation

## Completed

- Setup thủ công frontend Vite + React + TypeScript + Tailwind (giảm rủi ro lỗi cho agent/AI trong quá trình phát triển).
- Cấu trúc feature-based ở frontend: `api/`, `features/{auth,resources,taxonomy}/`, `layouts/`, `pages/`, `components/ui/`.
- Tạo Axios-based `apiClient` tập trung với JSON/form-urlencoded/multipart support, interceptor Bearer token và xử lý 401 redirect về `/login`.
- Triển khai `AuthContext` thật với state `user/token`, lưu token vào `localStorage`, gọi `GET /auth/me` khi có token, hỗ trợ `login/register/logout`.
- Hoàn thiện routing bằng `createBrowserRouter`, nested layout với `Outlet`, `ProtectedRoute` và `AdminRoute`.
- Scaffold các route public/protected/admin hiện có trong UI shell: `/`, `/login`, `/register`, `/departments/:id`, `/subjects/:id`, `/resources/:id`, `/me/resources`, `/resources/create`, `/resources/:id/upload`, `/admin/moderation`, `/admin/taxonomy`.
- Test thành công auth thật qua backend và phân quyền admin/user bằng tài khoản admin mặc định (seed từ `.env`, xem `core/config.py`).

## Phase Summary

1. Setup thủ công frontend để giảm rủi ro lỗi và giữ cây thư mục ổn định.
2. Tập trung vào API client và Auth flow thật với backend.
3. Hoàn thiện router, layout và scaffold toàn bộ màn hình shell cho các route public/protected/admin.

## Next Sprint

FE Catch-up Features

---

# Sprint 7

## Goal

FE Catch-up Features — nối API thật cho browse, personal resources, upload/submit-review, admin moderation và admin taxonomy

## Completed

- TanStack Query v5 + react-hot-toast + shared UI (`Spinner`, `ErrorMessage`, `PaginationBar`)
- Browse flow: Departments → Department detail → Major detail → Subject detail → Resource detail; `TaxonomyView` trên Home
- `/me/resources`, luồng create → upload → submit-review
- Admin moderation (approve/reject/delete) và admin taxonomy CRUD
- Query key factory, cache invalidation, `getApiErrorMessage`, validate URL param (`parseRouteId`)
- Backend phát sinh: filter `GET /majors/?department_id=`, `GET /subjects/?major_id=`, `GET /resources/me/{id}`, `GET /resources/admin`
- Audit/fix: taxonomy filter, cache invalidation, owner resource by ID, upload timeout, admin nav, i18n VI, dead code cleanup

## Next Sprint

Sprint 8

---

# Sprint 8

## Goal

Code Structure Refactor: Tách logic khỏi pages xuống feature hooks, thống nhất query key factory, gộp error handling, tạo DepartmentMajorSubjectPicker dùng chung, dọn barrel export, đồng bộ upload limit config FE/BE.

## Completed

- **Action-Based Hooks**: Tách các query/mutation hooks ở features/ resources và taxonomy.
- **DepartmentMajorSubjectPicker**: Component quản lý cascade khoa/ngành/môn tự động reset, thay thế logic trùng lặp ở TaxonomyView, ResourceCreatePage và AdminTaxonomyPage.
- **Upload Limit Configurations API**: Endpoint backend GET `/config/upload` expose limits cho hook `useUploadConfig` tiêu thụ, xóa sạch FE client settings.
- **Error Handling & Translations**: `AuthForm` sử dụng `getApiErrorMessage` và bổ sung localized translations trong `getApiErrorMessage.ts`.
- **Barrel Exports & Packaging**: Barrel `index.ts` cho resources feature và module component placement guidelines ở `features/README.md`.

## Decisions

- Đưa toàn bộ cấu trúc hooks về dạng feature-scoped.
- Component dùng một nơi giữ tại feature, dùng chung không có business logic chuyển về components/ui/.
- Sync dynamic config qua API Endpoint thay vì constants.

## Learned

- Cascade selection có nhiều corner case reset state cần xử lý thận trọng tại một component chung.
- Quản lý logic hooks giúp components chỉ làm render layout.

## Next Sprint

UI/UX Polish & Design Consistency

---

# Sprint 8.5

## Goal

Database Architecture Refactor: tách `Resource` dùng chung thành `Document` (Public) + `Notebook` (Private Workspace AI), dọn dẹp Frontend để build sạch.

## Completed

**Backend (Phase 1 & 2):**
- Xóa model `Resource` cũ, thay bằng `Document`, `Notebook`, `NotebookSavedDocument`, `Asset` (dùng `document_id`/`notebook_id` nullable + CHECK constraint loại trừ nhau)
- `DocumentStatus` enum (DRAFT/PUBLIC/DELETED); giữ `ResourceType` taxonomy
- API `/documents/`: `GET /documents/` (paginated, filter `subject_id` + `resource_type`), `GET /documents/{id}`, `GET /documents/{id}/assets/{asset_id}/download` (presigned MinIO URL — 15 phút, không cần JWT)
- `document_service.py`, `asset_service.py` — business logic tách khỏi router theo Service Layer pattern
- `storage_service.get_presigned_download_url()` hoạt động
- `seed.py` cập nhật chèn Document mẫu PUBLIC

**Frontend (Phase 3 — Cleanup):**
- `features/resources/api.ts`: types mới `Document`/`Asset`/`DocumentPageResponse`; 3 active API calls
- `features/resources/queryKeys.ts`: `documentsKeys` root `['documents']`; alias `resourcesKeys` giữ backwards-compat
- Hooks mới: `useDocuments`, `useDocumentDetail`
- 7 write/admin hooks cũ: stubbed (`export {}`), giữ trong repo
- `PublicResourceCard`: nhận `Document` prop
- `SubjectDetailPage`, `ResourceDetailPage`: consume Document API + nút Tải về presigned
- `MyResourcesPage`, `ResourceCreatePage`, `ResourceUploadPage`, `AdminModerationPage`: stubbed/notice
- `AppRouter`: routes Admin/contribution commented; alias `/documents/:id` thêm
- Nav links "Đóng góp tài liệu" ẩn ở `PublicLayout`, `AppLayout`, `HomePage`
- `npm run build` ✅ exit code 0

## Decisions

- Giữ tên thư mục `features/resources/` để tránh gãy import paths — chỉ update internals.
- Download file dùng presigned URL thay vì proxy backend — bỏ cần JWT, giảm tải server.
- Nhánh Admin (tạo/upload/moderation) tạm dừng, giữ file trong repo với `// [PAUSED - Admin branch]` comment.

## Learned

- `tsc --noEmit` có thể pass nhưng `vite build` vẫn fail nếu các file `.ts` unreachable từ exports vẫn tồn tại trong repo với broken imports — cần stub tất cả.
- Backwards-compat alias (`resourcesKeys = documentsKeys`) giúp tránh đổi import tại nhiều file cùng lúc.

## Next Sprint

UI/UX Polish & Design Consistency

---

# Sprint 9

## Goal

UI/UX Polish & Design Consistency: Chuẩn hóa, cải thiện UI/UX toàn bộ ứng dụng, áp dụng Progressive Disclosure (Home → Department → Major → Subject → Document), Việt hóa enums hiển thị, debounce tìm kiếm môn học tức thì không dấu và tích hợp PDF preview modal.

## Completed

- **Foundation Components**: Triển khai các UI component dùng chung có tính đồng bộ cao: `Badge.tsx`, `Breadcrumb.tsx`, `Card.tsx`, `EmptyState.tsx` trong `src/components/ui/`.
- **Page Refactoring (Progressive Disclosure Flow)**:
  - `HomePage`: Thay thế widget TaxonomyView 3 bước cũ bằng lưới card Department kèm thanh tìm kiếm môn học và nút liên kết đóng góp Google Form.
  - `DepartmentDetailPage`: Hiển thị danh sách card Major trực thuộc.
  - `MajorDetailPage`: Hiển thị chuyên đề Môn học theo khối kiến thức dưới dạng accordion nhóm (đáp ứng khối kiến thức ngành).
  - `SubjectDetailPage`: Danh sách tài liệu phẳng nằm ngang (Flat Document List) phân loại theo loại học liệu, hỗ trợ xem trước hoặc tải về trực tiếp.
  - `DocumentDetailPage`: Trang chi tiết hiển thị siêu dữ liệu tài liệu, frame xem trước PDF và nút tải về tệp tin CDN presigned.
- **Subject Search & Navbar Dropdown**: Debounce tìm kiếm không dấu/tiếng Việt (`SubjectSearchInput` sử dụng hook `useSearchSubjects`) được tích hợp tại Header trong `PublicLayout` và `AppLayout`, kết nối API `GET /subjects/?q=...` dùng ILIKE ở backend.
- **PDF Preview Modal**: Cho phép xem tệp PDF trực tiếp qua iframe từ CDN presigned URL (15 phút) của MinIO.
- **Feature Renaming & Modularization**: Di chuyển cấu trúc từ `src/features/resources` sang `src/features/documents` để nhất quán với Database model, dọn sạch code/hook thừa của luồng cũ.
- **Vietnamese Localizer**: Xây dựng bộ định dạng `src/utils/formatters.ts` hỗ trợ chuyển ngữ resource type, trạng thái của document và format relative time tiếng Việt.
- **Responsive Layout**: Hamburger toggle menu hoàn chỉnh cho mobile viewports.

## Decisions

- Độc lập ô tìm kiếm môn học và hộp thoại xem trước (PDF Preview Modal) thành các component feature-scoped riêng biệt.
- Sử dụng iframe trực tiếp kết hợp presigned URL của MinIO để tránh gánh nặng tải dung lượng cho backend của FastAPI.
- Loại bỏ toàn bộ các inline raw Tailwind form control ở các trang chi tiết/tạo mới để dùng chung UI components chuẩn hóa của hệ thống.

## Learned

- Giao diện phẳng (Flat List) giúp sinh viên tiếp cận tài liệu nhanh hơn so với card hiển thị phụ.
- Xử lý tìm kiếm không dấu ở database (PostgreSQL ILIKE tìm kiếm) là rất cần thiết cho ứng dụng tiếng Việt.

## Next Sprint

Core Feature Completion & Personal Workspace



