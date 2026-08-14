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

Chưa xác nhận

