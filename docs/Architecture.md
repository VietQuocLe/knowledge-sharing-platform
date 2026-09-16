# System Architecture & Technical Design

## Knowledge Sharing Platform

---

## 1. Tổng quan Kiến trúc Hệ thống (System Architecture Overview)

Hệ thống được thiết kế theo mô hình **Client-Server phân tầng hiện đại (Modern Multi-tier Architecture)**, tối ưu cho việc xử lý học liệu lớn và tích hợp mô hình ngôn ngữ lớn (LLM):

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT TIER                                     │
│   React 19 + TypeScript + Vite + Tailwind CSS + TanStack Query v5 + KaTeX  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ RESTful API / Server-Sent Events (SSE)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                           APPLICATION SERVER (FastAPI)                      │
│  ┌───────────────────────┬──────────────────────────┬────────────────────┐  │
│  │   Auth & RBAC         │   Public Resource Hub    │   AI Workspace     │  │
│  │  (Argon2id, JWT)      │   (Taxonomy & Library)   │  (Notebook Engine) │  │
│  ├───────────────────────┴──────────────────────────┴────────────────────┤  │
│  │                     RAG PIPELINE CORE ENGINE                          │  │
│  │  • Streaming Ingestion Generator (<30MB RAM)                          │  │
│  │  • Sentence-Aware Chunking (Underthesea + LlamaIndex)                 │  │
│  │  • SHA-256 Content-addressable Deduplication                          │  │
│  │  • Two-Stage Retrieval (Dense HNSW + Sparse GIN via RRF k=60)         │  │
│  │  • Cross-Encoder Reranker (Jina Reranker v2)                          │  │
│  │  • Quiz Studio Generator (Multi-Asset Linspace Sampling)              │  │
│  ├───────────────────────────────────────────────────────────────────────┤  │
│  │                     INTEGRATION & SECURITY LAYER                      │  │
│  │  • VNPay Sandbox 2.1.0 (HMAC-SHA512, Pessimistic Lock Idempotency)    │  │
│  │  • Object Storage Service (MinIO Presigned URL Engine)                │  │
│  │  • Observability & Tracing (Langfuse Cloud SDK v4)                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└───────────────────────┬───────────────────────────────┬─────────────────────┘
                        │                               │
┌───────────────────────▼──────────────┐ ┌──────────────▼─────────────────────┐
│       DATABASE & VECTOR ENGINE       │ │       OBJECT STORAGE (S3/MinIO)    │
│  PostgreSQL 16 + pgvector HNSW       │ │  MinIO / Cloudflare R2             │
│  • Relational Data (Users, Quotas)   │ │  • Original PDF & DOCX Assets      │
│  • Asset Embeddings (768d Cosine)    │ │  • Derived Preview PDFs            │
│  • Full-text Search Index (GIN)      │ │  • Presigned URL Streaming         │
└──────────────────────────────────────┘ └────────────────────────────────────┘
```

---

## 2. Kiến trúc Hai Phân vùng (Dual-Zone Architecture)

Để giải quyết mâu thuẫn giữa nhu cầu **chia sẻ tri thức cộng đồng** và **học tập cá nhân hóa sâu**, hệ thống phân tách logic thành 2 vùng:

1. **Vùng 1: Public Resource Hub (Thư viện công cộng)**
   - Tổ chức theo hình cây 3 cấp: **Khoa (Department) → Ngành (Major) → Môn học (Subject)**.
   - Tài liệu (`Document`) được gắn với Môn học và phân loại theo mục đích học tập (`SLIDE`, `EXAM`, `DOCUMENT`, `LECTURE`).
   - Tối ưu tra cứu nhanh bằng chỉ mục tiếng Việt không dấu (`unaccent`).
   - Người học có thể đọc trực tuyến (PDF preview) hoặc tải về qua Presigned URL có thời hạn.

2. **Vùng 2: Personal AI Workspace (Không gian Sổ tay cá nhân)**
   - Sổ tay (`Notebook`) thuộc sở hữu của từng cá nhân.
   - **Cơ chế Nguồn tài liệu kép (Dual-Source Binding):**
     - Lưu tài liệu từ Thư viện vào Sổ tay: tạo liên kết logic (`NotebookSavedDocument`), không nhân bản file nhị phân, không tốn thêm dung lượng lưu trữ.
     - Tải tệp cá nhân từ máy: tải trực tiếp vào sổ tay, kiểm tra mã độc qua magic-bytes, giới hạn 30MB/file.
   - **Chính sách hạn mức theo gói cước (Tier Soft-cap):**
     - Free: tối đa 8 nguồn tài liệu, 10 bài tập trắc nghiệm.
     - Pro: tối đa 20 nguồn tài liệu, 20 bài tập trắc nghiệm.
     - Cơ chế chặn mềm (Soft-cap): chỉ chặn thêm mới khi đã vượt hạn mức, tuyệt đối không bao giờ ẩn hay xóa tài liệu cũ của người dùng.

---

## 3. Kiến trúc Đường ống Xử lý Tài liệu (Ingestion Pipeline)

Quy trình nạp và bóc tách tài liệu diễn ra theo 5 bước tuần tự, được tối ưu nghiêm ngặt về bộ nhớ RAM và chi phí AI:

```text
[File Upload: PDF/DOCX]
        │
        ▼
[1. Conversion Guard] ──(DOCX)──> [LibreOffice Headless] ──> [Derived PDF]
        │
        ▼
[2. Streaming Text Extraction] ──> pypdfium2 generator (duy trì RAM < 30MB)
        │
        ▼
[3. Sentence-Aware Chunking] ───> Underthesea + LlamaIndex (500-700 tokens, 
        │                          không cắt vắt ngang ranh giới trang)
        ▼
[4. SHA-256 Deduplication] ─────> Trùng hash? ──(YES)──> Tái sử dụng Vector có sẵn
        │                                                     (Tiết kiệm 100% chi phí AI)
        │ (NO)
        ▼
[5. Dynamic Batch Embedding] ───> Gemini / Jina API (RateLimiter sliding-window)
        │
        ▼
[PostgreSQL pgvector] ──────────> Lưu bảng `AssetEmbedding` (Vector 768d + HNSW index)
```

---

## 4. Kiến trúc Động cơ Truy xuất Hai Tầng (Two-Stage Retrieval Engine)

Khi người học đặt câu hỏi trong Sổ tay, hệ thống thực hiện truy xuất thông tin qua 3 giai đoạn:

```text
[Câu hỏi của người học] + [Lịch sử hội thoại 6 lượt gần nhất]
        │
        ▼
[Query Condensation & Intent Routing] (Gemini 3.1 Flash Lite)
        │
        ├── Không cần tài liệu (Chit-chat/Cảm ơn) ──> Sinh phản hồi trực tiếp
        │
        └── Cần tra cứu tài liệu (needs_rag = true)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 1: HYBRID SEARCH RRF (Reciprocal Rank Fusion k=60)     │
│  • Dense Search Top-20: Vector Cosine HNSW (embedding 768d)  │
│  • Sparse Search Top-20: Full-text Search GIN (ts_rank_cd)  │
│  => Hợp nhất điểm số và chọn lọc Candidate Pool Top-15      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 2: CROSS-ENCODER RERANKING                            │
│  • Mô hình Jina Reranker v2 multilingual chấm điểm ngữ nghĩa│
│    trực tiếp giữa câu hỏi và từng chunk trong Pool Top-15   │
│  => Chọn lọc Top-5 kết quả liên quan nhất                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 3: HẬU XỬ LÝ & BẢO TOÀN NGỮ CẢNH (Post-processing)     │
│  • Adjacent Chunk Stitching: Tự động gộp chunk liền kề      │
│  • Token Budget Enforcement: Giới hạn tối đa 3,000 tokens    │
│  • Citation Renumbering: Đánh số lại trích dẫn [1]..[N]     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  GIAO THỨC SSE STREAMING (Server-Sent Events)               │
│  1. event: citations -> Bắn danh sách nguồn trước khi sinh từ│
│  2. event: delta     -> Truyền từng token text thời gian thực│
│  3. event: done      -> Hoàn tất, ghi DB user + assistant   │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Kiến trúc Cổng Thanh toán & Nâng cấp Pro (VNPay Gateway)

* **Giao thức:** VNPay Sandbox chuẩn 2.1.0, mã hóa ký số bảo mật bằng thuật toán **HMAC-SHA512**.
* **Cơ chế chống Race Condition & Idempotency Guard:**
  - Áp dụng kỹ thuật **Pessimistic Locking (`SELECT ... FOR UPDATE`)** trên bảng `PaymentOrder`.
  - Hỗ trợ cơ chế xác nhận kép: tiếp nhận Return URL khi người dùng quay lại trình duyệt và webhook IPN ngầm từ server VNPay, đảm bảo không bao giờ bị xử lý trùng lặp hay cộng sai hạn mức.
* **Cộng dồn thời gian (Stackable Expiry):** Nếu tài khoản còn hạn Pro, thời hạn 30 ngày mới sẽ được cộng nối tiếp từ mốc `pro_expires_at` hiện tại.
