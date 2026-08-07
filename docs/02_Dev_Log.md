# Sprint 1.2

## Goal

Backend Foundation

---

## Completed

- Config
- Database
- Main
- Health API

---

## Decisions

- SQLAlchemy thay SQLModel
- Chưa dùng Alembic

---

## Learned

- FastAPI Lifespan
- Dependency Injection
- SQLAlchemy Session

---

## Next Sprint

Authentication

---

# Sprint 2

## Goal

Authentication

---

## Completed

- Register
- Login
- Password Hashing
- JWT Authentication

---

## Decisions

- pwdlib (Argon2id) cho password hashing
- PyJWT cho access token
- Auth tách theo Service Layer

---

## Learned

- OAuth2PasswordBearer cho Bearer token flow
- JWT payload nên mang `sub` và `role`
- Service layer giữ business logic cho auth

---

## Next Sprint

Department + Major + Subject CRUD

---

# Sprint 3

## Goal

Department + Major + Subject CRUD

## Completed

- Department CRUD
- Major CRUD
- Subject CRUD
- Public read endpoints for Department/Major/Subject
- Admin-only write guard via dependency

## Decisions

- Router -> Service -> Model architecture for academic CRUD
- SQLAlchemy 2.0 `Session.execute(select(...))` for service queries
- Subject create/update resolves `major_ids` in service layer
- Department delete is restricted when related majors or subjects exist

## Learned

- Keep authorization in dependencies to keep routers thin
- Validate foreign keys in the service layer before mutating models
- Use lightweight nested response schemas to avoid circular imports

## Next Sprint

Resource & Asset Management

---

# Sprint 4

## Goal

Resource & Asset Management

## Completed

- Resource / Asset model split
- JSONB metadata-first schema
- ResourceType taxonomy update
- User.resources and Subject.resources rewired to Resource
- Resource CRUD API for admin writes
- Public read endpoints with pagination and subject filtering
- Soft delete via ResourceStatus.DELETED

## Decisions

- Resource is the metadata-first entity; Asset is the physical file layer
- JSONB is used for extensible metadata instead of new static columns
- Business logic remains in Service Layer; resource router now mirrors the Department/Major/Subject pattern

## Learned

- Model refactors should land before CRUD to reduce schema churn later
- Relationship rewiring must be updated together with exports to avoid stale imports
- Soft delete is the safer default for resource lifecycles because Sprint 6+ will attach embeddings and related derived data

## Next Sprint

Upload System & File Validation