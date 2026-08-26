# Dashboard

## Current Sprint

Sprint 11.5 — Document Conversion & Preview Debt Cleanup 🔄

---

## Last Completed

Sprint 11 — Notebook Detail Page & Document Saving / Asset Upload ✅

---

## Progress

Overall

93%

██████████████░░░

Backend

92%

Frontend

95%

---

## Next Task

Hoàn tất Sprint 11.5: tích hợp `libreoffice-writer` headless vào Dockerfile backend để convert DOCX → PDF khi upload, thêm cột `converted_pdf_path` cho `assets`, cho preview/download ưu tiên bản PDF phái sinh và mở khóa nút "Xem trước" cho DOCX ở cả Notebook cá nhân lẫn thư viện công cộng.

Kế tiếp — Sprint 12 (Ingestion Pipeline, backend only): bảng `AssetEmbedding` + index HNSW/GIN, trích xuất text bằng `pypdfium2`, page-aware chunking và embedding qua `gemini-embedding-001` (768d).

Nguyên tắc: mỗi sprint backend (11.5, 12, 13) phải có script test độc lập chạy xanh trước khi sang sprint kế tiếp.

---

## Current Problem

Không có blocker. Giao diện trang Workspace chi tiết chia cột, Quick Actions, quota, và các API lưu public document / upload tệp đã hoạt động ổn định và kiểm hợp thành công.

Nợ kỹ thuật đang xử lý ở Sprint 11.5: tài liệu DOCX chưa xem trước được (đang bị chặn bằng `isPreviewable` để tránh trình duyệt tải ngầm gây trắng màn hình), luồng preview/download chưa thống nhất giữa Notebook cá nhân và thư viện công cộng.
