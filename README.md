# Knowledge Sharing Platform - Nền tảng Chia sẻ Học liệu và Trợ lý AI

[![Deploy Status](https://img.shields.io/badge/Deploy-Live%20Demo-success)](https://knowledge-sharing-platform-six.vercel.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)


---

## 1. Giới thiệu tổng quan (Overview)

Knowledge Sharing Platform là hệ thống quản trị, chia sẻ tài liệu học tập đại học và hỗ trợ tự học chuyên sâu thông qua mô hình trợ lý AI cá nhân hóa (được phát triển dựa trên cảm hứng kết hợp giữa Studocu và NotebookLM).

Dự án giải quyết bài toán tiếp cận học liệu chính thống tại các trường đại học, đồng thời cung cấp công cụ tự học thông minh giúp sinh viên tra cứu tài liệu nhanh chóng, tự động tạo bài kiểm tra ôn tập và kiểm chứng độ chính xác của câu trả lời thông qua trích dẫn trang tài liệu.

### Điểm nhấn kỹ thuật nổi bật (Technical Highlights)
* **Kiến trúc hai phân vùng (Dual-Zone Architecture):** Tách biệt ranh giới giữa Public Resource Hub (thư viện học liệu phân cấp 3 tầng) và Personal AI Workspace (không gian sổ tay cá nhân). Hỗ trợ cơ chế liên kết nguồn tài liệu kép không trùng lặp dữ liệu vật lý.
* **Động cơ truy xuất hai tầng (Two-Stage Retrieval Engine):** Kết hợp Dense Vector Search (HNSW Cosine 768d) và Sparse Full-text Search (GIN index) qua công thức Reciprocal Rank Fusion (RRF, k=60) ở tầng 1, kết hợp mô hình Cross-Encoder Jina Reranker v2 ở tầng 2 để tái chấm điểm và chọn lọc Top-5 đoạn ngữ cảnh sát nhất với câu hỏi.
* **Trích dẫn nguồn chính xác theo từng trang (Page-level Grounded Citations):** AI stream câu trả lời qua giao thức Server-Sent Events (SSE) kèm nhãn trích dẫn; nhấp vào trích dẫn sẽ chuyển ngay đến trang PDF nguồn tương ứng (`#page=X`).
* **Ingestion Pipeline tiết kiệm tài nguyên:** Bóc tách văn bản streaming qua generator với `pypdfium2` kiểm soát RAM luôn dưới 30MB; chia đoạn theo ranh giới câu tiếng Việt; khử trùng lặp nội dung bằng mã băm SHA-256 để tiết kiệm 100% chi phí embedding khi tải lên tài liệu trùng lặp.
* **Xưởng bài tập trắc nghiệm (Quiz Studio):** Thuật toán Multi-Asset Linspace Sampling lấy mẫu đều các tài liệu trong sổ tay và gọi Gemini Structured JSON Output để sinh đề trắc nghiệm kèm giải thích.
* **Cổng thanh toán VNPay:** Tích hợp VNPay Sandbox 2.1.0 (ký HMAC-SHA512), áp dụng khóa bi quan (Pessimistic Lock `SELECT ... FOR UPDATE`) chống xử lý trùng đơn và quản lý nâng cấp gói cước Pro 30 ngày.

---

## 2. Liên kết hệ thống (Key Links)

* **Bản chạy thử nghiệm (Live Demo):** [https://knowledge-sharing-platform-six.vercel.app](https://knowledge-sharing-platform-six.vercel.app)
* **Tài liệu đặc tả yêu cầu (SRS):** [docs/SRS.md](./docs/SRS.md)
* **Thiết kế kiến trúc hệ thống:** [docs/Architecture.md](./docs/Architecture.md)
* **Kế hoạch & Kịch bản kiểm thử:** [docs/Test_Plan.md](./docs/Test_Plan.md)
* **Báo cáo đồ án (PDF):** [docs/report/](./docs/report/)

---

## 3. Công nghệ sử dụng (Tech Stack)

### Frontend
* React 19, TypeScript, Vite
* Tailwind CSS, Lucide React, KaTeX
* TanStack Query v5, Axios, React Router v7

### Backend
* FastAPI (Python 3.12), Pydantic v2
* SQLAlchemy 2.0, Alembic, PostgreSQL 16
* ARQ (Async Redis Queue) & Redis 7 (Background Task Processing)
* pgvector (HNSW Index), MinIO Object Storage
* Argon2id (`pwdlib`), JWT (HS256), Google OAuth 2.0

### AI & Xử lý ngôn ngữ tự nhiên
* Google Gemini 3.1 Flash Lite (Chat streaming, Intent Routing)
* Gemini Embedding 001 / Jina Embeddings v3 (768d MRL)
* Jina Reranker v2 (`jina-reranker-v2-base-multilingual`)
* `pypdfium2`, `underthesea`, `llama-index-core` (SentenceSplitter)
* Langfuse Cloud SDK v4 (Tracing & Token monitoring)

### Thanh toán & Hạ tầng
* VNPay Sandbox 2.1.0 HMAC-SHA512
* Docker & Docker Compose

---

## 4. Hướng dẫn Cài đặt & Khởi chạy (Getting Started)

### 4.1. Yêu cầu môi trường (Prerequisites)
* Docker & Docker Compose
* Python 3.12 trở lên
* Node.js 20 trở lên và npm
* Git

### 4.2. Khởi động cơ sở hạ tầng (Database & Object Storage)
Tại thư mục gốc của dự án:
```bash
docker compose up -d
```
Hệ thống khởi chạy 2 container:
* PostgreSQL 16 (hỗ trợ pgvector) lắng nghe tại cổng `5433` (tránh xung đột với cổng 5432 mặc định của máy).
* MinIO Object Storage lắng nghe tại cổng `9000` (API) và `9001` (Web Console).

> **Ghi chú:** Docker Compose trong dự án chỉ phục vụ khởi chạy hạ tầng (Database & Object Storage) với cấu hình mặc định sẵn sàng ngay mà không cần tạo trước file `.env`. Backend và Frontend được chạy trực tiếp trên máy cục bộ để tối ưu cho việc phát triển và gỡ lỗi (debug).

### 4.3. Cài đặt và chạy Backend
```bash
cd backend

# Khởi tạo và kích hoạt môi trường ảo Python
python -m venv .venv
# Trên Windows:
.\.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# Cấu hình biến môi trường
cp .env.example .env
# Chỉnh sửa file .env

# Khởi tạo dữ liệu mẫu
python scripts/seed_data.py

# Khởi chạy server FastAPI
uvicorn app.main:app --reload --port 8000

# Khởi chạy ARQ Background Worker (mở terminal riêng trong backend/):
python -m app.workers.worker
```
Backend API sẵn sàng tại: `http://localhost:8000`  
Swagger API Docs tại: `http://localhost:8000/docs`

### 4.4. Cài đặt và chạy Frontend
Mở một cửa sổ dòng lệnh mới:
```bash
cd frontend

# Cài đặt dependencies
npm install

# Cấu hình biến môi trường
cp .env.example .env

# Chạy ứng dụng
npm run dev
```
Giao diện người dùng truy cập tại: `http://localhost:5173`

---

## 5. Tài khoản thử nghiệm (Demo Accounts)

Sau khi chạy script `seed_data.py`, hệ thống khởi tạo sẵn các tài khoản sau để phục vụ nghiệm thu:

| Vai trò | Email đăng nhập | Mật khẩu | Quyền hạn & Chức năng kiểm thử |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin@ou.edu.vn` | `Admin@123456` | Toàn quyền quản lý danh mục Khoa, Ngành, Môn học tại `/admin/taxonomy` |
| **Người dùng mẫu (User)** | `user@ou.edu.vn` | `User@123456` | Sử dụng thư viện, Sổ tay cá nhân, hỏi đáp RAG và test nâng cấp Pro qua VNPay |

---

## 6. Kiểm thử hệ thống (Testing)

Hệ thống được tích hợp kiểm thử tự động toàn diện trên cả hai tầng:

### 6.1. Backend Unit & Integration Tests (39 kịch bản pytest)
```bash
cd backend
pytest -v
```

### 6.2. Frontend End-to-End Tests (Playwright Browser Automation)
```bash
cd frontend

# Cài đặt browser Chromium cho Playwright (chỉ cần chạy lần đầu tiên)
npx playwright install chromium

# Thực thi kiểm thử E2E
npm run test:e2e
```
*Chạy chế độ giao diện trực quan (UI mode):* `npm run test:e2e:ui`

Chi tiết kịch bản, dữ liệu đầu vào và kết quả kiểm thử được trình bày trong [docs/Test_Plan.md](./docs/Test_Plan.md).

---

## 7. Tài liệu kỹ thuật đi kèm (Documentation)

Bộ tài liệu kỹ thuật được lưu trữ tại thư mục `docs/`:
* [Software Requirements Specification (SRS)](./docs/SRS.md): Đặc tả yêu cầu phần mềm và luồng nghiệp vụ.
* [System Architecture](./docs/Architecture.md): Kiến trúc hệ thống, Ingestion pipeline và Two-Stage Retrieval.
* [Test Plan & Test Report](./docs/Test_Plan.md): Kế hoạch và kết quả kiểm thử 12 test suites.
* [Báo cáo đồ án & Slide](./docs/report/): Thư mục lưu trữ bản mềm báo cáo tốt nghiệp PDF.

---

## 8. Bản quyền & Giấy phép (License)

Dự án được phân phối dưới giấy phép mã nguồn mở [MIT License](./LICENSE). Mọi tài liệu và thư viện mở tích hợp trong hệ thống đều tuân thủ giấy phép sử dụng tương ứng.