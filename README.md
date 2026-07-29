# Knowledge Sharing Platform

> AI-powered knowledge sharing platform for managing, sharing, and learning from academic resources.

---

## Overview

Knowledge Sharing Platform is a graduation project that aims to build a modern learning resource platform integrated with AI-powered learning assistance.

Inspired by Studocu, the system enables users to organize, share, and interact with learning materials through Retrieval-Augmented Generation (RAG), providing a more personalized and intelligent learning experience.

---

## Features

### Public Resource Hub

- Academic resource management
- Department & Subject organization
- Public document sharing
- Search and browse learning resources

### Personal Workspace

- Personal document management
- AI-powered document chat
- RAG-based question answering
- AI-generated summaries
- AI-generated quizzes *(planned)*

---

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

### Backend

- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- pgvector
- MinIO

### AI

- LangChain
- OpenAI API
- Sentence Transformers

---

## Project Structure

```text
knowledge-sharing-platform/

├── backend/
├── frontend/
├── docs/
└── README.md
```

---

# Getting Started

## Prerequisites

- Python 3.12+
- Node.js 22+
- Docker Desktop
- Git

---

## Clone Repository

```bash
git clone https://github.com/your-username/knowledge-sharing-platform.git

cd knowledge-sharing-platform
```

---

## Backend Setup

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configure Environment

Create a `.env` file inside `backend/`.

Example:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=knowledge_sharing_platform
POSTGRES_PORT=5433

MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

---

## Start Infrastructure

```bash
docker compose up -d
```

This starts:

- PostgreSQL
- MinIO

---

## Run Backend

```bash
uvicorn app.main:app --reload
```

Backend will be available at:

```
http://localhost:8000
```

Swagger UI:

```
http://localhost:8000/docs
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```
http://localhost:5173
```

---

## Documentation

Project documentation is available in the `docs/` directory.

Important documents:

- `PROJECT_CONTEXT.md`
- `00_Dashboard.md`
- `03_Architecture.md`
- `10_System_Design.md`

---

## Roadmap

The project follows an iterative development process.

Core milestones include:

- Backend Foundation
- Authentication
- Learning Resource Management
- Upload System
- AI Pipeline
- Personal Workspace
- RAG Chat
- Testing & Deployment

---

## License

This project is developed for educational purposes as a university graduation project.