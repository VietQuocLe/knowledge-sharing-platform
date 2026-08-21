# Quy tắc tổ chức Component (Feature Architecture Guidelines)

Để đảm bảo tính mô-đun hóa và tránh lặp lại hoặc phân rã mã nguồn không rõ ràng (như tình trạng của `PaginationBar` hay `PublicResourceCard`), toàn bộ các components trong dự án phải tuân theo quy tắc phân chia địa lý sau:

## 1. Feature-Specific Components
- **Vị trí**: `frontend/src/features/<tên_feature>/components/`
- **Mô tả**: Toàn bộ các component chỉ phục vụ trực tiếp cho một feature nhất định, có phụ thuộc logic nghiệp vụ (business logic), query hooks của chính feature đó.
- **Ví dụ**: `PublicResourceCard` hay `DepartmentMajorSubjectPicker` chỉ thuộc về nghiệp vụ tài nguyên và bộ chọn phân lớp ngành học.

## 2. Global Shared UI Components
- **Vị trí**: `frontend/src/components/ui/`
- **Mô tả**: Các component dùng chung toàn app, không chứa hoặc phụ thuộc vào logic nghiệp vụ của bất kỳ feature cụ thể nào (stateless hoặc chỉ chứa UI-state đơn giản).
- **Ví dụ**: `Button`, `Input`, `Spinner`, `ErrorMessage`, `PaginationBar`.
