# PROJECT_CONTEXT.md

# Knowledge Sharing Platform

> Graduation Project - AI-powered Knowledge Sharing Platform inspired by Studocu + NotebookLM

---

# 1. Project Overview

## Description

Knowledge Sharing Platform là hệ thống chia sẻ tài liệu học tập kết hợp AI, lấy cảm hứng từ Studocu và NotebookLM.

Mục tiêu của đồ án không phải clone Studocu mà xây dựng một nền tảng cho phép:

- Chia sẻ tài liệu học tập
- Quản lý tài liệu theo Khoa → Môn học
- Upload PDF, DOCX,...
- AI đọc tài liệu
- AI trả lời câu hỏi dựa trên tài liệu
- Notebook cá nhân
- Personal Knowledge Base
- Public Knowledge Hub

Đây là đồ án cá nhân.

---

# 2. Current Progress

Current Sprint

> Sprint 1.2 — Backend Foundation

Overall Progress

15%

Status

🟢 Active Development

---

# 3. Current Sprint Goal

Hoàn thành nền tảng Backend trước khi phát triển các chức năng.

Mục tiêu Sprint:

- Thiết kế Project Structure
- Docker
- PostgreSQL
- MinIO
- SQLAlchemy
- FastAPI
- Config System
- Database Connection
- Health API

---

# 4. Completed

## Backend

- Project Structure
- SQLAlchemy Models
- Database Connection
- Config Management
- FastAPI Main
- Health API

## Infrastructure

- Docker Compose
- PostgreSQL
- MinIO

## Database Models

- User
- Department
- Subject
- LearningResource

---

# 5. Next Task

Sprint 2

Authentication

Bao gồm:

- Register
- Login
- Password Hashing
- JWT Authentication

Sau Authentication sẽ tiếp tục:

- Subject CRUD
- Learning Resource CRUD
- Upload
- AI Pipeline

---

# 6. Technology Stack

## Backend

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- pgvector
- MinIO

## Frontend

- React
- Vite
- Tailwind CSS

## AI

- LangChain
- OpenAI API
- Sentence Transformers
- pgvector

---

# 7. Current Project Structure

```
knowledge-sharing-platform/

backend/
frontend/
docs/

README.md
```

Backend

```
app/

api/
core/
models/
schemas/
services/

main.py
```

---

# 8. Backend Architecture

```
Client

↓

FastAPI

↓

API Router

↓

Service Layer

↓

SQLAlchemy Models

↓

PostgreSQL

↓

MinIO (Storage)
```

Business Logic luôn nằm trong Service Layer.

Router chỉ nhận Request và trả Response.

---

# 9. Coding Principles

Luôn tuân theo các nguyên tắc sau.

## Architecture

- Service Layer Architecture
- Separation of Concerns
- Clean Code
- Single Responsibility Principle

## Không được

❌ Query Database trong Router

❌ Business Logic trong Router

❌ SQL trong API

❌ Code trùng lặp

❌ Hardcode Config

---

# 10. Technology Decisions

Đã thống nhất:

## ORM

SQLAlchemy 2.0

Không sử dụng SQLModel.

---

## Database

PostgreSQL

---

## Vector Database

pgvector

Không dùng Pinecone.

---

## Object Storage

MinIO

---

## Migration

Hiện tại sử dụng

Base.metadata.create_all()

Alembic sẽ tích hợp sau nếu còn thời gian.

---

## Primary Key

Integer

Không dùng UUID.

---

## API Version

Chưa sử dụng

api/v1

Đợi khi project đủ lớn mới tách version.

---

# 11. Roadmap

Sprint 1

✅ Backend Foundation

↓

Sprint 2

Authentication

↓

Sprint 3

Department + Subject

↓

Sprint 4

Learning Resource

↓

Sprint 5

Upload System

↓

Sprint 6

AI Pipeline

↓

Sprint 7

Notebook Workspace

↓

Sprint 8

RAG Chat

↓

Sprint 9

Testing

↓

Sprint 10

Deployment & Optimization

---

# 12. AI Features (Planned)

Document Upload

↓

Chunking

↓

Embedding

↓

pgvector

↓

Retriever

↓

LLM

↓

Notebook Chat

↓

Citation

↓

Summary

↓

Flashcards (Optional)

↓

Quiz Generation (Optional)

---

# 13. Development Workflow

Mỗi Sprint sẽ theo quy trình:

Planning

↓

Implementation

↓

Testing

↓

Documentation

↓

Commit

↓

Push GitHub

---

# 14. Git Convention

Commit theo Sprint hoặc Feature.

Ví dụ:

feat: initialize backend foundation

feat: implement authentication

feat: add upload module

feat: integrate rag pipeline

Không commit kiểu:

update

fix

abc

123

---

# 15. AI Collaboration Instructions

Nếu AI đọc file này, hãy:

- Hiểu toàn bộ bối cảnh project trước khi trả lời.
- Không đề xuất thay đổi kiến trúc nếu không thật sự cần.
- Ưu tiên giữ code đơn giản, dễ hiểu và phù hợp với đồ án đại học.
- Giải thích ngắn gọn nhưng đúng bản chất.
- Hướng dẫn theo từng Sprint, không nhảy quá xa.
- Khi đề xuất cấu trúc hoặc thư viện mới, giải thích lý do sử dụng.
- Luôn ưu tiên tính ổn định và khả năng hoàn thành đồ án đúng tiến độ.

---

# 16. Current Status

Current Sprint

Sprint 1.2

Current Module

Backend Foundation

Next Module

Authentication

Current Focus

Xây dựng nền tảng Backend ổn định trước khi phát triển AI Pipeline.

---

# 17. Notes

Đây là đồ án cá nhân.

Mục tiêu lớn nhất không phải sử dụng thật nhiều công nghệ, mà là:

- Xây dựng một hệ thống hoàn chỉnh.
- Hiểu rõ kiến trúc của từng thành phần.
- Có khả năng giải thích mọi quyết định thiết kế khi bảo vệ đồ án.
- Dành phần lớn thời gian cho AI (RAG, Notebook, pgvector) thay vì sa đà vào hạ tầng không cần thiết.

Mọi đề xuất nên cân bằng giữa tính thực tế, độ phức tạp và thời gian hoàn thành của một sinh viên thực hiện trong một học kỳ.