from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models import Base, Department, Document, Major, Subject, User
from app.models.enums import DocumentStatus, ResourceType
from app.schemas.auth import RegisterRequest
from app.schemas.department import DepartmentCreate
from app.schemas.major import MajorCreate
from app.schemas.subject import SubjectCreate
from app.services import auth_service, department_service, major_service, subject_service
from app.services.startup_service import ensure_admin_exists

logger = logging.getLogger(__name__)

SEED_DEPARTMENT_NAME = "Khoa Công nghệ thông tin"
SEED_MAJOR_CODE = "CNTT"
SEED_MAJOR_NAME = "Công nghệ thông tin"
SEED_SUBJECTS = [
    {"code": "PY101", "name": "Lập trình Python"},
    {"code": "DB101", "name": "Cơ sở dữ liệu"},
]
SEED_USER_EMAIL = "user@example.com"
SEED_USER_PASSWORD = "User12345!"
SEED_USER_FULL_NAME = "Test User"

SEED_DOCUMENTS = [
    {
        "subject_code": "PY101",
        "title": "Đề thi giữa kỳ Python",
        "description": "Đề thi giữa kỳ môn Lập trình Python — câu hỏi trắc nghiệm và tự luận.",
        "resource_type": ResourceType.EXAM,
    },
    {
        "subject_code": "PY101",
        "title": "Slide giới thiệu Python",
        "description": "Bộ slide bài giảng tuần 1–3: cú pháp cơ bản, kiểu dữ liệu, vòng lặp.",
        "resource_type": ResourceType.SLIDE,
    },
    {
        "subject_code": "PY101",
        "title": "Tài liệu tham khảo Python",
        "description": "Tổng hợp ghi chú và ví dụ minh họa cho sinh viên tự ôn.",
        "resource_type": ResourceType.DOCUMENT,
    },
    {
        "subject_code": "DB101",
        "title": "Đề thi SQL cơ bản",
        "description": "Đề kiểm tra trắc nghiệm về SELECT, JOIN và aggregate functions.",
        "resource_type": ResourceType.EXAM,
    },
    {
        "subject_code": "DB101",
        "title": "Slide chuẩn hóa cơ sở dữ liệu",
        "description": "Bài giảng về normal forms (1NF–3NF) kèm ví dụ thực tế.",
        "resource_type": ResourceType.SLIDE,
    },
    {
        "subject_code": "DB101",
        "title": "Bài tập thiết kế ERD",
        "description": "Bộ bài tập thiết kế ERD cho hệ thống thư viện và cửa hàng online.",
        "resource_type": ResourceType.DOCUMENT,
    },
]


def _get_department_by_name(db) -> Department | None:
    return next((department for department in department_service.get_all(db) if department.name == SEED_DEPARTMENT_NAME), None)


def _get_major_by_code(db) -> Major | None:
    return next((major for major in major_service.get_all(db) if major.code == SEED_MAJOR_CODE), None)


def _get_subject_by_code(db, code: str) -> Subject | None:
    return next((subject for subject in subject_service.get_all(db) if subject.code == code), None)


def _get_admin_user(db) -> User:
    admin = db.execute(select(User).where(User.email == settings.ADMIN_EMAIL)).scalar_one_or_none()
    if admin is None:
        raise RuntimeError(f"Admin user not found: {settings.ADMIN_EMAIL}. Run app startup first.")
    return admin


def seed_department(db) -> Department:
    department = _get_department_by_name(db)
    if department is not None:
        logger.info("Department already exists: %s", department.name)
        return department

    department = department_service.create(db, DepartmentCreate(name=SEED_DEPARTMENT_NAME))
    logger.info("Created department: %s", department.name)
    return department


def seed_major(db, department_id: int) -> Major:
    major = _get_major_by_code(db)
    if major is not None:
        logger.info("Major already exists: %s", major.code)
        return major

    major = major_service.create(
        db,
        MajorCreate(
            code=SEED_MAJOR_CODE,
            name=SEED_MAJOR_NAME,
            department_id=department_id,
        ),
    )
    logger.info("Created major: %s", major.code)
    return major


def seed_subjects(db, department_id: int, major_id: int) -> list[Subject]:
    seeded_subjects: list[Subject] = []
    for subject_data in SEED_SUBJECTS:
        existing_subject = _get_subject_by_code(db, subject_data["code"])
        if existing_subject is not None:
            logger.info("Subject already exists: %s", existing_subject.code)
            seeded_subjects.append(existing_subject)
            continue

        subject = subject_service.create(
            db,
            SubjectCreate(
                code=subject_data["code"],
                name=subject_data["name"],
                department_id=department_id,
                major_ids=[major_id],
            ),
        )
        logger.info("Created subject: %s", subject.code)
        seeded_subjects.append(subject)

    return seeded_subjects


def seed_user(db) -> User:
    existing_user = db.execute(
        select(User).where(User.email == SEED_USER_EMAIL)
    ).scalar_one_or_none()
    if existing_user is not None:
        logger.info("User already exists: %s", existing_user.email)
        return existing_user

    auth_service.register_user(
        db,
        RegisterRequest(
            email=SEED_USER_EMAIL,
            full_name=SEED_USER_FULL_NAME,
            password=SEED_USER_PASSWORD,
        ),
    )
    user = db.execute(select(User).where(User.email == SEED_USER_EMAIL)).scalar_one()
    logger.info("Created user: %s", user.email)
    return user


def seed_documents(db, admin_user: User) -> list[Document]:
    seeded_documents: list[Document] = []

    for document_data in SEED_DOCUMENTS:
        subject = _get_subject_by_code(db, document_data["subject_code"])
        if subject is None:
            raise RuntimeError(f"Subject not found for seed document: {document_data['subject_code']}")

        existing_document = db.execute(
            select(Document).where(
                Document.title == document_data["title"],
                Document.subject_id == subject.id,
            )
        ).scalar_one_or_none()
        if existing_document is not None:
            logger.info("Document already exists: %s", existing_document.title)
            seeded_documents.append(existing_document)
            continue

        document = Document(
            title=document_data["title"],
            description=document_data["description"],
            subject_id=subject.id,
            created_by=admin_user.id,
            resource_type=document_data["resource_type"],
            status=DocumentStatus.PUBLIC,
        )
        db.add(document)
        db.flush()
        logger.info("Created document: %s (%s)", document.title, document.resource_type.value)
        seeded_documents.append(document)

    return seeded_documents


def seed() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        department = seed_department(db)
        major = seed_major(db, department.id)
        seed_subjects(db, department.id, major.id)
        seed_user(db)
        ensure_admin_exists(db)
        admin_user = _get_admin_user(db)
        seed_documents(db, admin_user)
        db.commit()
        logger.info("Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
