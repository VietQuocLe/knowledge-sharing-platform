# Knowledge Sharing Platform

> **Đồ án tốt nghiệp ngành Công nghệ Thông tin**  
> Nền tảng chia sẻ học liệu đại học kết hợp trợ lý AI học tập thông minh (lấy cảm hứng từ Studocu & NotebookLM).

---

## 1. Giới thiệu tổng quan (Overview)

**Knowledge Sharing Platform** là hệ thống quản trị và chia sẻ tài liệu học tập đại học kết hợp không gian làm việc AI cá nhân hóa. Dự án giải quyết trọn vẹn bài toán từ việc tổ chức phân cấp học liệu chính quy đến hỗ trợ sinh viên tự học sâu:

* **Public Resource Hub (Thư viện công cộng):** Học liệu được tổ chức theo cây đào tạo 3 cấp: **Khoa → Ngành → Môn học → Tài liệu**. Hỗ trợ tìm kiếm môn học tức thì không dấu, phân loại tài liệu (`SLIDE`, `EXAM`, `DOCUMENT`, `LECTURE`), xem trước trực tuyến (PDF/DOCX) và tải tài liệu an toàn qua Presigned URL MinIO.
* **AI Notebook Workspace (Sổ tay cá nhân):** Không gian làm việc riêng tư cho phép sinh viên liên kết tài liệu từ thư viện hoặc tải lên tài liệu cá nhân để nghiên cứu.
* **Trợ lý hỏi đáp RAG thông minh:** Động cơ Two-Stage Retrieval (Dense Vector HNSW + Full-text Search GIN hợp nhất qua RRF, kết hợp Cross-Encoder Reranker) cho phép hỏi đáp ngữ cảnh chuyên sâu, truyền dữ liệu thời gian thực qua SSE stream và dẫn nguồn chính xác theo từng trang (`#page=X`).
* **Xưởng bài tập trắc nghiệm (Quiz Studio):** Thuật toán Multi-Asset Linspace Sampling tự động sinh bộ câu hỏi trắc nghiệm kiểm tra kiến thức từ nhiều tài liệu cùng lúc kèm giải thích chi tiết.
* **Cổng thanh toán VNPay:** Tích hợp VNPay Sandbox 2.1.0 ký HMAC-SHA512, cơ chế khóa bi quan (Pessimistic Lock) chống trùng lặp giao dịch để nâng cấp gói tài khoản Pro mở rộng hạn mức.

---

## 2. 📚 Hồ sơ Tài liệu Kỹ thuật (Documentation)

Bộ tài liệu kỹ thuật chi tiết của đồ án được tổ chức tại thư mục [`docs/`](./docs/):

* 📋 **[Software Requirements Specification (SRS)](./docs/SRS.md):** Đặc tả toàn diện yêu cầu nghiệp vụ, yêu cầu chức năng 6 phân hệ, yêu cầu phi chức năng và ma trận phân quyền.
* 🏛️ **[System Architecture & Technical Design](./docs/Architecture.md):** Thiết kế kiến trúc tổng thể, sơ đồ Dual-Zone, chi tiết Ingestion Pipeline, Động cơ Two-Stage Retrieval và thiết kế CSDL.
* 🧪 **[Test Plan & Test Report](./docs/Test_Plan.md):** Kế hoạch kiểm thử, ma trận kịch bản test và báo cáo kết quả chi tiết của 12 Test Suites tự động Backend (100% Passed).
* 📁 **[Project Reports & Slides](./docs/report/):** Thư mục lưu trữ bản mềm báo cáo tốt nghiệp chính thức và slide bảo vệ.

---

## 3. Công nghệ sử dụng (Technology Stack)

### Frontend
* **Core:** React 19, TypeScript, Vite
* **Styling & UI:** Tailwind CSS, Lucide React, KaTeX (render công thức toán học)
* **State & Data Fetching:** TanStack Query v5 (React Query), Axios
* **Routing:** React Router v7 (Nested Layouts, Protected & Admin Guards)

### Backend
* **Core Framework:** FastAPI (Python 3.12), Pydantic v2
* **Database & ORM:** PostgreSQL 16, pgvector (HNSW index Cosine 768d), SQLAlchemy 2.0, Alembic
* **Object Storage:** MinIO (S3-compatible Object Storage), Presigned URL Service
* **Security & Auth:** Argon2id (`pwdlib`), JWT (HS256), Google OAuth 2.0

### AI & RAG Engine
* **Large Language Model:** Google Gemini 3.1 Flash Lite (Chat streaming & Intent Routing)
* **Embedding Model:** `gemini-embedding-001` / `jina-embeddings-v3` (768d MRL)
* **Cross-Encoder Reranker:** `jina-reranker-v2-base-multilingual`
* **Text Processing & Chunking:** `pypdfium2` (generator streaming RAM < 30MB), `underthesea`, `llama-index-core`
* **Observability:** Langfuse Cloud SDK v4

### Tích hợp thanh toán
* **Cổng thanh toán:** VNPay Sandbox chuẩn 2.1.0, mã hóa chữ ký số HMAC-SHA512, Pessimistic Locking (`SELECT FOR UPDATE`).

---

## 4. Hướng dẫn Cài đặt & Khởi chạy (Getting Started)

### 4.1. Yêu cầu môi trường (Prerequisites)
* Docker & Docker Compose
* Python 3.12+
* Node.js 20+ & npm

---

### 4.2. Khởi động Hạ tầng Docker (Database & Storage)

Tại thư mục gốc của dự án:

```bash
# Khởi động PostgreSQL (kèm pgvector) và MinIO Object Storage
docker compose up -d
```

* **PostgreSQL:** `localhost:5433` (DB: `knowledge_sharing_platform`, User: `postgres`, Password: `postgres`)
* **MinIO Console:** `http://localhost:9001` (User: `minioadmin`, Password: `minioadmin`)

---

### 4.3. Cài đặt & Khởi chạy Backend

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Khởi tạo môi trường ảo Python
python -m venv .venv

# Kích hoạt môi trường ảo:
# Trên Windows (PowerShell):
.\.venv\Scripts\activate
# Trên Linux/macOS:
source .venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 4. Thiết lập file cấu hình môi trường
# Copy từ .env.example sang .env
cp .env.example .env
# Mở file .env và điền GOOGLE_API_KEY của bạn

# 5. Nạp dữ liệu mẫu ban đầu (Khoa, Ngành, Môn học, Tài liệu học tập)
python scripts/seed_data.py

# 6. Khởi chạy server FastAPI
uvicorn app.main:app --reload --port 8000
```

* Backend API: `http://localhost:8000`
* Swagger API Documentation: `http://localhost:8000/docs`

---

### 4.4. Cài đặt & Khởi chạy Frontend

Mở một cửa sổ terminal mới:

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt dependencies
npm install

# 3. Thiết lập file cấu hình môi trường
cp .env.example .env

# 4. Khởi chạy ứng dụng với Vite
npm run dev
```

* Giao diện người dùng: `http://localhost:5173`

---

## 5. Tài khoản Thử nghiệm Mặc định (Demo Accounts)

Sau khi chạy lệnh `python scripts/seed_data.py`, hệ thống tự động cung cấp 2 tài khoản sẵn sàng để hội đồng nghiệm thu và kiểm thử:

| Tài khoản | Email đăng nhập | Mật khẩu | Quyền hạn / Gói cước |
| :--- | :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin@ou.edu.vn` | `Admin@123456` | Toàn quyền CRUD Khoa, Ngành, Môn học |
| **Người học mẫu (User Demo)** | `user@ou.edu.vn` | `User@123456` | Người học thông thường, có thể nâng cấp Pro qua VNPay |

---

## 6. Kiểm thử Tự động (Automated Testing)

Dự án đi kèm bộ kiểm thử tự động toàn diện với 12 test suites phủ kín các phân hệ:

```bash
cd backend
# Kích hoạt .venv nếu chưa kích hoạt
pytest -v
```

Chi tiết kịch bản từng ca kiểm thử xem tại [`docs/Test_Plan.md`](./docs/Test_Plan.md).