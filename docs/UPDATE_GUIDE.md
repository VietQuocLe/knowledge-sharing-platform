# Documentation Workflow

## Sau mỗi buổi code (< 2 phút)

- [ ] Cập nhật `PROJECT_CONTEXT.md`
  - Current Task
  - Completed
  - Next Task (nếu thay đổi)

- [ ] Nếu thay đổi ảnh hưởng API, model, storage hoặc tiến độ: rà soát các tài liệu liên quan trong `docs/` (Dashboard, Roadmap, Dev Log, Architecture, System Design), không chỉ `PROJECT_CONTEXT.md`.

- [ ] Commit

- [ ] Push GitHub

---

## Sau khi hoàn thành một Sprint (~5 phút)

- [ ] Cập nhật `00_Dashboard.md`
- [ ] Thêm Sprint mới vào `02_Dev_Log.md`
- [ ] Cập nhật `03_Architecture.md` (nếu kiến trúc thay đổi)
- [ ] Cập nhật `10_System_Design.md` (nếu schema, role, storage hoặc scope triển khai thay đổi)
- [ ] Commit với message theo Sprint
- [ ] Push GitHub

---

## Khi có thay đổi lớn

- [ ] Cập nhật `README.md`
- [ ] Cập nhật `PROJECT_CONTEXT.md`

Hãy đóng vai Project Assistant.

Dựa trên code thực tế và những gì vừa hoàn thành trong buổi làm việc này:

1. Liệt kê và rà soát toàn bộ file trong `docs/` có liên quan.
2. Cập nhật PROJECT_CONTEXT.md và các tài liệu có nội dung lỗi thời.
3. Nếu Sprint đã hoàn thành thì cập nhật Dashboard, Roadmap và Sprint Log.
4. Đề xuất commit message theo Conventional Commits.
5. Liệt kê checklist trước khi push GitHub.

Giữ cấu trúc và văn phong của từng tài liệu; không thay đổi phần không liên quan.
