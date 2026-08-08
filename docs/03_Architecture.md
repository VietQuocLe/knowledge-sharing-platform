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
- Resource public list/detail chỉ trả resource `PUBLIC` chưa bị xóa; list yêu cầu `subject_id` và phân trang theo `created_at DESC, id DESC`.
- `GET /resources/me`, tạo resource, upload asset và submit review yêu cầu JWT; chủ sở hữu hoặc admin được upload/submit. Cập nhật/xóa resource và approve public là admin-only.
- Upload đi theo `Router → resource_service → storage_service → MinIO`: chỉ PDF/DOCX hợp lệ, kiểm tra giới hạn cấu hình, ghi object theo `resources/{resource_id}/{uuid}_{filename}`, rồi tạo `Asset`; lỗi commit DB sẽ cố gắng xóa object vừa ghi.
- Khi tạo, user thường có thể để mặc định `PRIVATE` hoặc chọn trực tiếp `PENDING_REVIEW` để đóng góp vào hàng chờ duyệt; chỉ admin được tạo trực tiếp `PUBLIC`. Luồng review từ resource private vẫn là `PRIVATE → PENDING_REVIEW → PUBLIC`; soft delete dùng `ResourceStatus.DELETED`.
