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
- `src/features/{auth,documents,taxonomy}/` — mỗi feature có `api.ts`, `queryKeys.ts` (documents/taxonomy), `components/`
- `src/layouts/` — `PublicLayout`, `AppLayout`, `AdminLayout`
- `src/pages/` — page components; lắp ráp UI và wiring TanStack Query (logic mutation/query hiện nằm tại đây)
- `src/components/ui/` — `Button`, `Input`, `Modal`, `Spinner`, `ErrorMessage`, `PaginationBar`
- `src/components/` — `AdminNavLinks`, `ProtectedRoute`, `AdminRoute`
- `src/utils/` — `parseRouteId`

### API Layer

- `apiClient` dùng Axios: JSON, form-urlencoded (OAuth2 login), multipart (upload asset)
- Request interceptor gắn `Authorization: Bearer <token>` từ `localStorage`
- Response interceptor xử lý `401` bằng cách xóa token và redirect về `/login`
- Upload asset dùng timeout riêng 120s (`features/documents/api.ts`)

### Auth Layer

- `AuthContext` quản lý `user`, `token`, `isLoading`
- Token lưu vào `localStorage`
- Khi có token, gọi `GET /auth/me` để lấy user hiện tại
- Login/register/logout hoạt động với backend; `ProtectedRoute` / `AdminRoute` bảo vệ route

### Routing

- `createBrowserRouter` với nested layout qua `<Outlet/>`
- Route hiện có:
  - Public: `/`, `/login`, `/register`, `/departments`, `/departments/:id`, `/majors/:id`, `/subjects/:id`, `/documents/:id`
  - Protected: (các tính năng Workspace / tài liệu cá nhân tạm ẩn chuẩn bị cho Sprint 10+)
  - Admin: `/admin/taxonomy` (link `/admin/moderation` tạm ẩn chờ kích hoạt lại)
- User `ADMIN` thấy link Phân loại trên `PublicLayout` và sidebar `AppLayout`

### State & Forms

- TanStack Query cho server state (list/detail, admin moderation, taxonomy CRUD)
- Query key factory: `features/documents/queryKeys.ts`, `features/taxonomy/queryKeys.ts`
- Cache invalidation sau mutation (create/upload/submit, admin approve/reject/delete, taxonomy CRUD)
- `react-hook-form` cho login/register
- `react-hot-toast` cho feedback mutation; `getApiErrorMessage` parse `detail` từ backend

---

## Current Notes

- Router chỉ nhận request và trả response; business logic nằm trong Service Layer.
- JWT Bearer qua `OAuth2PasswordBearer`; `security.py` xử lý hash và token.
- Mô hình học thuật: `Department → Major → Subject → Document`.
- Taxonomy GET hỗ trợ filter: `GET /majors/?department_id=`, `GET /subjects/?major_id=` (optional).
- Document public list/detail chỉ trả `PUBLIC` chưa xóa; list yêu cầu `subject_id` (được tối giản hóa sang Flat List để tránh click trung gian nhiều lớp).
- Model Asset liên kết với Document hoặc Notebook (XOR constraint). Mỗi Document đi kèm đúng 1 Asset (quan hệ 1:1).
- Admin: Duy trì API và route `/admin/taxonomy` cho danh mục.
- Backend cung cấp API GET `/config/upload` để lấy thông tin giới hạn file size và kiểu file cho phép.
- Visibility: `PRIVATE → PENDING_REVIEW → PUBLIC`; trạng thái hoạt động của Document dùng `DocumentStatus` (DRAFT, PUBLIC, DELETED).
- Sprint 7 hoàn thành: toàn bộ luồng browse, personal resources, upload/submit, admin moderation/taxonomy đã nối API thật.

---

### Tính năng bổ sung ngoài Roadmap gốc (Sprint 8.5/9)

1. **Subject Search API & Dropdown:** Hỗ trợ tìm kiếm nhanh theo môn học (Vietnamese tone-insensitive) qua API `GET /subjects/?q=...` tích hợp debounce và dropdown instant search tại Header.
2. **PDF Preview Modal:** Cho phép xem trực tiếp nội dung tệp PDF của tài liệu (sử dụng presigned CDN URL có thời hạn 15 phút của MinIO) trong Modal mà không cần tải về máy.
3. **Flat Document List:** Tối ưu hóa UI browse môn học hiển thị danh sách tài liệu dẹt phẳng nằm ngang, hiển thị trực tiếp Badge & thông tin phân loại, hỗ trợ xem trực tiếp hoặc tải về ngay trên dòng.
