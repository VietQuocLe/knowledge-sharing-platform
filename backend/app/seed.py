from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import Base, Department, Major, Subject, User
from app.schemas.auth import RegisterRequest
from app.schemas.department import DepartmentCreate
from app.schemas.major import MajorCreate
from app.schemas.subject import SubjectCreate
from app.services import auth_service, department_service, major_service, subject_service

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


def _get_department_by_name(db) -> Department | None:
    return next((department for department in department_service.get_all(db) if department.name == SEED_DEPARTMENT_NAME), None)


def _get_major_by_code(db) -> Major | None:
    return next((major for major in major_service.get_all(db) if major.code == SEED_MAJOR_CODE), None)


def _get_subject_by_code(db, code: str) -> Subject | None:
    return next((subject for subject in subject_service.get_all(db) if subject.code == code), None)


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


def seed() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        department = seed_department(db)
        major = seed_major(db, department.id)
        seed_subjects(db, department.id, major.id)
        seed_user(db)
        db.commit()
        logger.info("Seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()