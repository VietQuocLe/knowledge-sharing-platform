Client

↓

FastAPI App

↓

API Router

↓

Dependencies / Auth Guard

↓

Service Layer

↓

SQLAlchemy Models

↓

PostgreSQL

↓

MinIO (Storage)

---

## Frontend Architecture

### Stack

- React 19 + Vite 8 + TypeScript
- Tailwind CSS v3
- TanStack Query v5, react-hot-toast
- Không dùng UI library ngoài; component cơ bản tự viết trong `components/ui/`
- `tsconfig` cấu hình lỏng với `strict=false` và `noImplicitAny=false` nhằm giữ tốc độ phát triển MVP

### Folder Structure

- `src/api/` — `apiClient`, `getApiErrorMessage`
- `src/features/{auth,resources,taxonomy}/` — mỗi feature có `api.ts`, `queryKeys.ts` (resources/taxonomy), `components/`
- `src/layouts/` — `PublicLayout`, `AppLayout`, `AdminLayout`
- `src/pages/` — page components; lắp ráp UI và wiring TanStack Query (logic mutation/query hiện nằm tại đây)
- `src/components/ui/` — `Button`, `Input`, `Modal`, `Spinner`, `ErrorMessage`, `PaginationBar`
- `src/components/` — `AdminNavLinks`, `ProtectedRoute`, `AdminRoute`
- `src/utils/` — `parseRouteId`

### API Layer

- `apiClient` dùng Axios: JSON, form-urlencoded (OAuth2 login), multipart (upload asset)
- Request interceptor gắn `Authorization: Bearer <token>` từ `localStorage`
- Response interceptor xử lý `401` bằng cách xóa token và redirect về `/login`
- Upload asset dùng timeout riêng 120s (`features/resources/api.ts`)

### Auth Layer

- `AuthContext` quản lý `user`, `token`, `isLoading`
- Token lưu vào `localStorage`
- Khi có token, gọi `GET /auth/me` để lấy user hiện tại
- Login/register/logout hoạt động với backend; `ProtectedRoute` / `AdminRoute` bảo vệ route

### Routing

- `createBrowserRouter` với nested layout qua `<Outlet/>`
- Route hiện có:
  - Public: `/`, `/login`, `/register`, `/departments`, `/departments/:id`, `/majors/:id`, `/subjects/:id`, `/resources/:id`
  - Protected: `/me/resources`, `/resources/create`, `/resources/:id/upload`
  - Admin: `/admin/moderation`, `/admin/taxonomy`
- User `ADMIN` thấy link Kiểm duyệt / Phân loại trên `PublicLayout` và sidebar `AppLayout`

### State & Forms

- TanStack Query cho server state (list/detail, admin moderation, taxonomy CRUD)
- Query key factory: `features/resources/queryKeys.ts`, `features/taxonomy/queryKeys.ts`
- Cache invalidation sau mutation (create/upload/submit, admin approve/reject/delete, taxonomy CRUD)
- `react-hook-form` cho login/register và form tạo resource
- `react-hot-toast` cho feedback mutation; `getApiErrorMessage` parse `detail` từ backend

---

## Current Notes

- Router chỉ nhận request và trả response; business logic nằm trong Service Layer.
- JWT Bearer qua `OAuth2PasswordBearer`; `security.py` xử lý hash và token.
- Mô hình học thuật: `Department → Major → Subject → Resource`.
- Taxonomy GET hỗ trợ filter: `GET /majors/?department_id=`, `GET /subjects/?major_id=` (optional).
- Resource public list/detail chỉ trả `PUBLIC` chưa xóa; list yêu cầu `subject_id`.
- `GET /resources/me`, `GET /resources/me/{resource_id}`, create, upload, submit-review yêu cầu JWT.
- Admin: `GET /resources/admin`, approve, reject, update, delete.
- Upload: PDF/DOCX qua backend proxy → MinIO; giới hạn cấu hình qua Settings.
- Visibility: `PRIVATE → PENDING_REVIEW → PUBLIC`; soft delete `ResourceStatus.DELETED`.
- Sprint 7 hoàn thành: toàn bộ luồng browse, personal resources, upload/submit, admin moderation/taxonomy đã nối API thật.
