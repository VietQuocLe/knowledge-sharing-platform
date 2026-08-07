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

## Current Notes

- Router chỉ nhận request và trả response.
- Business logic nằm trong Service Layer.
- Authentication hiện tại dùng JWT Bearer token qua `OAuth2PasswordBearer`.
- `security.py` xử lý password hashing và token creation/decoding.
- Mô hình học thuật hiện tại đi qua `Department -> Major -> Subject`.
- Các route ghi dữ liệu cho Department/Major/Subject dùng admin dependency, còn GET endpoints vẫn public.
- CRUD của Department/Major/Subject được xử lý trong Service Layer, không query DB trong Router.
- Resource hiện cũng theo cùng pattern: GET public, POST/PUT/DELETE admin-only, soft delete bằng `ResourceStatus.DELETED`, và list public có pagination theo `created_at DESC`.