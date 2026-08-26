Sprint 1

Backend Foundation — ✅ done

↓

Sprint 2

Authentication — ✅ done

↓

Sprint 3

Department + Major + Subject — ✅ done

↓

Sprint 4

Resource (DB Refactor & CRUD) — ✅ done

↓

Sprint 5

Upload System & Visibility Workflow — ✅ done

↓

Sprint 6

✅ FE Foundation

↓

Sprint 7

✅ FE Catch-up Features

↓

Sprint 8

Code Structure Refactor — ✅ done

↓

Sprint 8.5

Database Architecture Refactor (Document/Notebook/Asset split) — ✅ done

↓

Sprint 9

UI/UX Polish & Design Consistency — ✅ done

↓

Sprint 10

Notebook (AI Workspace) Feature — Dashboard + Layout Redesign — ✅ done

↓

Sprint 10.5

Notebook Dashboard Actions (Rename/Delete) — ✅ done

↓

Sprint 11

Notebook Detail Page & Document Saving / Asset Upload — ✅ done

↓

Sprint 11.5

Document Conversion & Preview Debt Cleanup (LibreOffice headless DOCX → PDF, `converted_pdf_path`, mở khóa preview DOCX) — 🔄 in progress

↓

Sprint 12

Ingestion Pipeline (Backend only) — bảng `AssetEmbedding`, `pypdfium2` page-aware chunking, `gemini-embedding-001` (768d), index HNSW/GIN — ⏳ kế hoạch

↓

Sprint 13

Retrieval Engine & Chat API (Backend only) — Hybrid Search RRF (Dense + Sparse), Intent Routing/Condensation qua `gemini-3.5-flash-lite`, SSE streaming kèm trích dẫn trang — ⏳ kế hoạch

↓

Sprint 14

Chat Frontend & Citation UI — chat ở cột phải `NotebookDetailPage`, streaming, `CitationBadge` nhảy thẳng trang PDF (`#page=X`) — ⏳ kế hoạch

↓

Sprint 15

Quiz & Flashcards Studio — Native Tool Calling sinh trắc nghiệm/flashcards từ `selected_asset_ids` — ⏳ kế hoạch

↓

Sprint 16

Testing — unit/integration test backend, test luồng chính frontend, seed/fixture cho demo — ⏳ kế hoạch

↓

Sprint 17

Deployment & Optimization — Docker hóa production, chuyển Cloud (Vercel/Render/Supabase/R2) qua `.env`, tối ưu chi phí token — ⏳ kế hoạch

---

Lý do tách sprint AI/RAG: mỗi sprint từ 11.5 đến 17 phải tự kiểm thử độc lập (sprint backend 11.5, 12, 13 có script test riêng chạy xanh) trước khi bắt đầu sprint kế tiếp — theo đúng pattern Sprint 11, tránh gom nhiều tầng vào một sprint gây khó debug và khó rollback.

