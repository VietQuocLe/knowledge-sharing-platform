# Software Requirements Specification (SRS)

## Knowledge Sharing Platform — Nền tảng Chia sẻ Học liệu Tích hợp AI

---

## 1. Giới thiệu tổng quan (Introduction)

### 1.1. Mục đích tài liệu
Tài liệu Đặc tả Yêu cầu Phần mềm (SRS) này mô tả toàn diện các yêu cầu nghiệp vụ, yêu cầu chức năng, yêu cầu phi chức năng và kiến trúc ca sử dụng của hệ thống **Knowledge Sharing Platform**. Tài liệu phục vụ làm căn cứ nghiệm thu đồ án tốt nghiệp ngành Công nghệ Thông tin.

### 1.2. Bối cảnh & Tầm nhìn sản phẩm
Trong môi trường giáo dục đại học, sinh viên thường gặp khó khăn trong việc tìm kiếm tài liệu học tập chính thống theo từng môn học và thiếu một công cụ cá nhân hóa để tra cứu sâu, tự ôn tập hiệu quả. 

**Knowledge Sharing Platform** được xây dựng với mục tiêu giải quyết bài toán trên thông qua kiến trúc hai phân vùng độc lập (Dual-Zone Architecture):
1. **Public Resource Hub (Thư viện học liệu công cộng):** Tổ chức, phân loại và chia sẻ tài liệu học tập theo cấu trúc phân cấp đào tạo chính quy: Khoa (Department) → Ngành (Major) → Môn học (Subject) → Tài liệu (Document).
2. **AI Workspace (Không gian học tập cá nhân):** Cung cấp các Sổ tay cá nhân (Notebooks) cho phép người học lưu trữ học liệu từ thư viện hoặc tải lên tài liệu cá nhân, tích hợp trợ lý AI thông minh qua kỹ thuật RAG (Retrieval-Augmented Generation) để hỏi đáp có dẫn chứng trang tài liệu chính xác và tự động sinh bài tập trắc nghiệm ôn tập (Quiz Studio).

---

## 2. Tác nhân & Phân quyền Hệ thống (Actors & Roles)

Hệ thống phân quyền dựa trên vai trò (Role-Based Access Control - RBAC) kết hợp mô hình gói cước (Subscription Tier):

| Tác nhân (Actor) | Mô tả vai trò & Quyền hạn |
| :--- | :--- |
| **Khách (Guest)** | Người dùng chưa đăng nhập; chỉ xem danh mục Khoa, Ngành, Môn học, danh sách tài liệu công cộng và xem trước trang đầu. |
| **Người dùng (User - Free Tier)** | Người dùng đã đăng nhập; có quyền truy cập toàn bộ tài liệu công cộng, tạo Sổ tay cá nhân (Notebook), hỏi đáp RAG và sinh bài tập trắc nghiệm trong hạn mức Free (tối đa 8 nguồn tài liệu / sổ tay, 10 bài tập trắc nghiệm). |
| **Người dùng Pro (User - Pro Tier)** | Người dùng đã nâng cấp qua cổng thanh toán VNPay; mở rộng hạn mức lên tới 20 nguồn tài liệu / sổ tay và 20 bài tập trắc nghiệm, thời hạn sử dụng 30 ngày. |
| **Quản trị viên (Admin)** | Quản lý toàn bộ danh mục đào tạo (CRUD Khoa, Ngành, Môn học), quản trị người dùng và giám sát hệ thống. |

---

## 3. Đặc tả Yêu cầu Chức năng (Functional Requirements)

### Phân hệ 1: Xác thực & Quản lý Tài khoản (Authentication & Account)
* **FR-AUTH-01 (Đăng ký/Đăng nhập chuẩn):** Đăng ký tài khoản bằng Email, mật khẩu được băm an toàn qua thuật toán Argon2id; cấp Access Token JWT (thời hạn 24 giờ).
* **FR-AUTH-02 (Google OAuth 2.0):** Hỗ trợ đăng nhập một chạm qua Google ID Token (`@react-oauth/google`), tự động khởi tạo hoặc liên kết tài khoản.
* **FR-AUTH-03 (Remember Me):** Quản lý lưu trữ phiên linh hoạt qua `localStorage` (duy trì phiên) hoặc `sessionStorage` (phiên tạm thời).

### Phân hệ 2: Thư viện Học liệu Công cộng (Public Resource Hub)
* **FR-PUB-01 (Cấu trúc phân cấp đào tạo):** Phân loại học liệu theo cây 3 cấp: Khoa → Ngành → Môn học.
* **FR-PUB-02 (Tìm kiếm môn học thông minh):** Tìm kiếm tức thì môn học theo mã môn hoặc tên tiếng Việt không phân biệt dấu (unaccent accent-insensitive matching).
* **FR-PUB-03 (Phân loại tài liệu):** Phân loại tài liệu theo nhóm: `SLIDE` (Bài giảng), `EXAM` (Đề thi), `DOCUMENT` (Giáo trình/Tài liệu), `LECTURE` (Tài liệu nghe giảng).
* **FR-PUB-04 (Xem trước tài liệu):** Hỗ trợ xem trước tài liệu PDF trực tuyến trên trình duyệt. Tự động chuyển đổi tài liệu DOCX sang PDF phái sinh để phục vụ xem trước.
* **FR-PUB-05 (Tải tài liệu an toàn):** Cấp Presigned URL từ MinIO Object Storage (thời hạn 15 phút) để tải file trực tiếp, giảm tải cho application server.

### Phân hệ 3: Không gian Sổ tay Cá nhân (AI Notebook Workspace)
* **FR-NOTE-01 (Quản lý Sổ tay):** Cho phép người học tạo, đổi tên, xóa mềm sổ tay cá nhân.
* **FR-NOTE-02 (Nguồn tài liệu kép - Dual Source):** Một sổ tay có thể chứa nguồn tài liệu từ:
  1. *Học liệu công cộng:* Lưu liên kết logic từ thư viện vào sổ tay mà không nhân bản file vật lý.
  2. *Học liệu cá nhân:* Tải file PDF/DOCX trực tiếp từ máy (giới hạn 30MB, kiểm định magic bytes).
* **FR-NOTE-03 (Chính sách hạn mức mềm - Soft-cap Quota):**
  - Gói Free: Tối đa 8 nguồn tài liệu / sổ tay, 10 bài tập trắc nghiệm.
  - Gói Pro: Tối đa 20 nguồn tài liệu / sổ tay, 20 bài tập trắc nghiệm.
  - Không bao giờ ẩn hay xóa tài liệu cũ của người dùng khi hết hạn Pro; chỉ chặn khi người dùng muốn thêm mới vượt hạn mức.

### Phân hệ 4: Trợ lý Học tập RAG & Hỏi đáp (RAG Chat Assistant)
* **FR-RAG-01 (Ingestion Pipeline):** Trích xuất text từng trang độc lập dạng generator (RAM < 30MB), chia đoạn ngữ nghĩa theo ranh giới câu (SentenceSplitter tiếng Việt), tính mã băm SHA-256 để chống trùng lặp embedding (Deduplication).
* **FR-RAG-02 (Two-Stage Retrieval):**
  - *Tầng 1 (Hybrid Search RRF):* Kết hợp Dense Search HNSW (vector 768d) và Sparse Search GIN Full-text Search qua Reciprocal Rank Fusion ($k=60$) để trích xuất Top-15 chunk phù hợp nhất.
  - *Tầng 2 (Cross-Encoder Reranking):* Dùng mô hình Jina Reranker v2 để chấm điểm lại mức độ liên quan ngữ nghĩa và lọc ra Top-5 chunk tối ưu.
* **FR-RAG-03 (SSE Streaming Chat):** Truyền kết quả phản hồi của AI theo thời gian thực qua giao thức Server-Sent Events (SSE) gồm 4 sự kiện: `citations`, `delta`, `done`, `error`.
* **FR-RAG-04 (Trích dẫn nguồn chính xác theo trang):** Mọi câu trả lời của AI đều kèm nhãn trích dẫn `[1]`, `[2]`. Khi người học click vào trích dẫn, hệ thống tự động nhảy đến đúng trang PDF nguồn tương ứng (`#page=X`).

### Phân hệ 5: Xưởng Bài tập Trắc nghiệm (Quiz Studio)
* **FR-QUIZ-01 (Sinh bài tập trắc nghiệm tự động):** Áp dụng thuật toán Multi-Asset Linspace Sampling để chọn lọc đại diện đều các đoạn văn bản từ tất cả tài liệu được chọn trong sổ tay; gọi mô hình Gemini Structured Output sinh bộ câu hỏi trắc nghiệm kèm giải thích chi tiết.
* **FR-QUIZ-02 (Trình làm bài thi tương tác QuizRunner):** Giao diện làm bài trực quan, chọn đáp án, tính điểm tức thì, xem lời giải chi tiết và trích dẫn trang tài liệu tương ứng.

### Phân hệ 6: Thanh toán & Quản lý Gói cước (VNPay Payment)
* **FR-PAY-01 (Tạo đơn hàng nâng cấp Pro):** Tạo yêu cầu thanh toán gói Pro (50,000 VNĐ / 30 ngày) chuyển hướng an toàn sang cổng VNPay Sandbox 2.1.0 (ký HMAC-SHA512).
* **FR-PAY-02 (Xử lý giao dịch an toàn & Idempotency):** Khóa dòng đơn hàng bằng Pessimistic Lock (`SELECT ... FOR UPDATE`), xác thực kép qua cả Return URL và IPN webhook ngầm, đảm bảo không bao giờ cộng hạn mức hai lần.
* **FR-PAY-03 (Cộng dồn thời hạn):** Nâng cấp thêm 30 ngày vào thời điểm hết hạn hiện tại nếu người dùng vẫn đang trong thời gian Pro.

---

## 4. Đặc tả Yêu cầu Phi chức năng (Non-Functional Requirements)

* **NFR-PERF-01 (Bộ nhớ tiết kiệm):** Bộ nhớ RAM tiêu thụ của backend khi xử lý chuyển đổi và bóc tách tài liệu PDF/DOCX luôn được kiểm soát dưới 30MB nhờ giải phóng tài nguyên C-layer ngay sau mỗi trang.
* **NFR-PERF-02 (Thời gian phản hồi):** Quá trình Two-Stage Retrieval (Dense + Sparse + Reranker) hoàn thành dưới 1.5 giây; token đầu tiên của luồng chat SSE phản hồi dưới 2.5 giây.
* **NFR-SEC-01 (Bảo mật thông tin):** Mật khẩu mã hóa Argon2id; không lưu khóa bí mật trong mã nguồn; xác thực token JWT chuẩn RFC 7519; xác thực chữ ký số thanh toán HMAC-SHA512 chống giả mạo đơn hàng.
* **NFR-SEC-02 (Kiểm định tệp an toàn):** Kiểm tra magic bytes của toàn bộ file tải lên nhằm ngăn chặn mã độc giả dạng phần mở rộng file.
* **NFR-COMP-01 (Tương thích & Khả năng quan sát):** Frontend hoạt động trơn tru trên mọi trình duyệt hiện đại (Chrome, Edge, Firefox, Safari); Backend tích hợp đầy đủ Langfuse SDK theo dõi chi phí token, độ trễ và vết thực thi AI.
