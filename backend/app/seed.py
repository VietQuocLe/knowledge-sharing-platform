from __future__ import annotations

import logging
import sys

from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models import Base, Department, Document, Major, Subject, User, Asset
from app.models.enums import DocumentStatus, ResourceType, SubjectCategory
from app.models.major import major_subject
from app.schemas.auth import RegisterRequest
from app.schemas.department import DepartmentCreate
from app.schemas.major import MajorCreate
from app.schemas.subject import SubjectCreate
from app.services import auth_service, department_service, major_service, subject_service
from app.services.startup_service import ensure_admin_exists
from app.services.storage_service import get_minio_client, upload_object

logger = logging.getLogger(__name__)

SEED_DEPARTMENT_NAME = "Khoa Công nghệ thông tin"
SEED_MAJOR_CODE = "CNTT"
SEED_MAJOR_NAME = "Công nghệ thông tin"

SEED_SUBJECTS = [
    # GENERAL (Đại cương)
    {"code": "MATH1313", "name": "Đại số tuyến tính", "category": SubjectCategory.GENERAL},
    {"code": "MATH1314", "name": "Giải tích", "category": SubjectCategory.GENERAL},
    {"code": "MATH1315", "name": "Xác suất và thống kê", "category": SubjectCategory.GENERAL},
    {"code": "ITEC1401", "name": "Nhập môn tin học", "category": SubjectCategory.GENERAL},
    {"code": "POLI1304", "name": "Triết học Mác - Lênin", "category": SubjectCategory.GENERAL},
    {"code": "GLAW1315", "name": "Pháp luật đại cương", "category": SubjectCategory.GENERAL},

    # FOUNDATION (Cơ sở ngành)
    {"code": "ITEC1505", "name": "Cơ sở lập trình", "category": SubjectCategory.FOUNDATION},
    {"code": "ITEC1504", "name": "Kỹ thuật lập trình", "category": SubjectCategory.FOUNDATION},
    {"code": "MISY2501", "name": "Cấu trúc dữ liệu và thuật giải", "category": SubjectCategory.FOUNDATION},
    {"code": "ITEC2504", "name": "Lập trình hướng đối tượng", "category": SubjectCategory.FOUNDATION},
    {"code": "ITEC2502", "name": "Cơ sở dữ liệu", "category": SubjectCategory.FOUNDATION},
    {"code": "ITEC2503", "name": "Mạng máy tính", "category": SubjectCategory.FOUNDATION},
    {"code": "ITEC1310", "name": "Hệ điều hành và kiến trúc máy tính", "category": SubjectCategory.FOUNDATION},
    {"code": "MATH2402", "name": "Toán rời rạc", "category": SubjectCategory.FOUNDATION},

    # SPECIALIZED (Chuyên ngành)
    {"code": "ITEC4409", "name": "Công nghệ phần mềm", "category": SubjectCategory.SPECIALIZED},
    {"code": "ITEC3401", "name": "Phân tích thiết kế hệ thống", "category": SubjectCategory.SPECIALIZED},
    {"code": "ITEC3412", "name": "An toàn hệ thống thông tin", "category": SubjectCategory.SPECIALIZED},
    {"code": "ITEC4402", "name": "Quản trị hệ cơ sở dữ liệu", "category": SubjectCategory.SPECIALIZED},
    {"code": "ITEC4403", "name": "Quản trị mạng", "category": SubjectCategory.SPECIALIZED},
    {"code": "ITEC4415", "name": "Kiểm thừ phần mềm", "category": SubjectCategory.SPECIALIZED},
    {"code": "ITEC3413", "name": "Trí tuệ nhân tạo", "category": SubjectCategory.SPECIALIZED},

    # ELECTIVE_CAPSTONE (Tự chọn & Tốt nghiệp)
    {"code": "ITEC3403", "name": "Lập trình Web", "category": SubjectCategory.ELECTIVE_CAPSTONE},
    {"code": "ITEC4417", "name": "Lập trình trên thiết bị di động", "category": SubjectCategory.ELECTIVE_CAPSTONE},
    {"code": "ITEC4416", "name": "Điện toán đám mây", "category": SubjectCategory.ELECTIVE_CAPSTONE},
    {"code": "ITEC4401", "name": "Đồ án ngành", "category": SubjectCategory.ELECTIVE_CAPSTONE},
    {"code": "ITEC4899", "name": "Thực tập tốt nghiệp", "category": SubjectCategory.ELECTIVE_CAPSTONE},
    {"code": "ITEC4699", "name": "Khóa luận tốt nghiệp", "category": SubjectCategory.ELECTIVE_CAPSTONE},
]

SEED_USER_EMAIL = "user@example.com"
SEED_USER_PASSWORD = "User12345!"
SEED_USER_FULL_NAME = "Test User"

SEED_DOCUMENTS = [
    # MISY2501 (Cấu trúc dữ liệu và thuật giải)
    {
        "subject_code": "MISY2501",
        "title": "Slide bài giảng Cấu trúc dữ liệu và giải thuật (Đại học Khoa học Tự nhiên)",
        "description": "Bộ bài giảng chi tiết bao gồm danh sách liên kết, ngăn xếp, hàng đợi, cây nhị phân và các giải thuật sắp xếp.",
        "resource_type": ResourceType.LECTURE,
        "assets": [
            {
                "file_name": "Slide_CTDL_GT.pdf",
                "file_path": "documents/misy2501/Slide_CTDL_GT.pdf",
                "file_type": "application/pdf",
                "size": 2450000,
            }
        ],
    },
    {
        "subject_code": "MISY2501",
        "title": "Đề thi cấu trúc dữ liệu và thuật giải cuối kỳ 2024",
        "description": "Bộ câu hỏi thi cuối kì kèm đáp án tham khảo dạng viết code và lý thuyết.",
        "resource_type": ResourceType.EXAM,
        "assets": [
            {
                "file_name": "DeThi_CTDL_CuoiKy_2024.pdf",
                "file_path": "documents/misy2501/DeThi_CTDL_CuoiKy_2024.pdf",
                "file_type": "application/pdf",
                "size": 1820000,
            }
        ],
    },
    # ITEC2502 (Cơ sở dữ liệu)
    {
        "subject_code": "ITEC2502",
        "title": "Slide chuẩn hóa cơ sở dữ liệu và đại số quan hệ",
        "description": "Bài học về chuẩn hóa cơ sở dữ liệu (1NF-3NF, BCNF) cùng đại số quan hệ toán học.",
        "resource_type": ResourceType.LECTURE,
        "assets": [
            {
                "file_name": "Slide_ChuanHoaCSDL.pdf",
                "file_path": "documents/itec2502/Slide_ChuanHoaCSDL.pdf",
                "file_type": "application/pdf",
                "size": 3120000,
            }
        ],
    },
    {
        "subject_code": "ITEC2502",
        "title": "Bài tập lớn lập trình thiết kế ERD bệnh viện",
        "description": "Yêu cầu thiết kế thực thể liên kết ERD và chuyển sang mô hình quan hệ cho bài toán quản lý bệnh viện.",
        "resource_type": ResourceType.REFERENCE,
        "assets": [
            {
                "file_name": "BTL_ThietKeERD_BenhVien.docx",
                "file_path": "documents/itec2502/BTL_ThietKeERD_BenhVien.docx",
                "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "size": 1050000,
            }
        ],
    },
    # ITEC1505 (Cơ sở lập trình)
    {
        "subject_code": "ITEC1505",
        "title": "Bài tập thực hành tuần 1 - 5 nhập môn lập trình C/C++",
        "description": "Đề bài tập thực hành nhập môn gồm cấu trúc điều kiện, vòng lặp và xử lý mảng cơ bản.",
        "resource_type": ResourceType.REFERENCE,
        "assets": [
            {
                "file_name": "ThucHanh_C_Tuan1_5.docx",
                "file_path": "documents/itec1505/ThucHanh_C_Tuan1_5.docx",
                "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "size": 950000,
            }
        ],
    },
    # ITEC1504 (Kỹ thuật lập trình)
    {
        "subject_code": "ITEC1504",
        "title": "Tài liệu mẫu môn Kỹ thuật lập trình C/C++",
        "description": "Tài liệu hướng dẫn thực hành lập trình C++ nâng cao cấu trúc con trỏ, mảng động, tệp tin và đệ quy.",
        "resource_type": ResourceType.REFERENCE,
        "assets": [
            {
                "file_name": "ky_thuat_lap_trinh_sample.pdf",
                "file_path": "documents/itec1504/ky_thuat_lap_trinh_sample.pdf",
                "file_type": "application/pdf",
                "size": 0,
                "seed_asset_source": "app/seed_assets/ky_thuat_lap_trinh_sample.pdf",
            }
        ],
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
        # Update the association table category column
        db.execute(
            update(major_subject)
            .where(
                major_subject.c.subject_id == subject.id,
                major_subject.c.major_id == major_id
            )
            .values(category=subject_data["category"])
        )
        logger.info("Created subject: %s with category %s", subject.code, subject_data["category"].value)
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

        # Seed Assets for this document if specified
        if "assets" in document_data:
            for asset_data in document_data["assets"]:
                import os
                seed_asset_source = asset_data.get("seed_asset_source")
                file_size = asset_data["size"]
                if seed_asset_source and os.path.exists(seed_asset_source):
                    file_size = os.path.getsize(seed_asset_source)

                asset = Asset(
                    document_id=document.id,
                    file_name=asset_data["file_name"],
                    file_path=asset_data["file_path"],
                    file_type=asset_data["file_type"],
                    size=file_size,
                )
                db.add(asset)
                db.flush()
                logger.info("Created asset record: %s", asset.file_name)

                # Try/except upload
                try:
                    if seed_asset_source and os.path.exists(seed_asset_source):
                        with open(seed_asset_source, "rb") as f:
                            file_data = f.read()
                        logger.info("Using real file content from: %s", seed_asset_source)
                    else:
                        file_data = f"Mock file content for {asset.file_name}. Dedicated to Knowledge Sharing Platform.".encode("utf-8")

                    upload_object(
                        object_path=asset.file_path,
                        data=file_data,
                        content_type=asset.file_type,
                    )
                    logger.info("Uploaded file to MinIO: %s", asset.file_path)
                except Exception as e:
                    logger.warning("Failed to upload asset file for %s to MinIO: %s", asset.file_name, e)

    return seeded_documents


def seed() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # 1. MinIO connection check
    try:
        client = get_minio_client()
        client.list_buckets()
        logger.info("MinIO connection verified successfully.")
    except Exception as e:
        logger.error(
            "CRITICAL ERROR: Failed to connect to MinIO. Please ensure MinIO is running (e.g. docker-compose up minio).\nDetails: %s",
            e
        )
        sys.exit(1)

    # 2. Recreate DB
    logger.info("Dropping and recreating database schemas...")
    Base.metadata.drop_all(bind=engine)
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
