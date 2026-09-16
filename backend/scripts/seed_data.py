from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path

from sqlalchemy import select, update, text
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    Base,
    Department,
    Major,
    Subject,
    Document,
    Asset,
    User,
)
from app.models.major import major_subject
from app.models.notebook import Notebook, NotebookSavedDocument
from app.models.notebook_chat import NotebookChatSession, NotebookChatMessage
from app.models.artifact import NotebookArtifact
from app.models.enums import (
    UserRole,
    SubjectCategory,
    ResourceType,
    DocumentStatus,
    AssetConversionStatus,
    AssetIngestionStatus,
    ChatMessageRole,
    ArtifactType,
)
from app.services.storage_service import get_minio_client, upload_object
from app.services.ingestion_service import ingest_asset
from app.services.conversion_service import convert_docx_to_pdf_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed_data")

# ─── CONSTANTS & CONFIGURATION ────────────────────────────────────────────────

SEED_ADMIN_EMAIL = settings.ADMIN_EMAIL
SEED_ADMIN_PASSWORD = settings.ADMIN_PASSWORD
SEED_ADMIN_FULL_NAME = settings.ADMIN_FULL_NAME

SEED_USER_EMAIL = "user@ou.edu.vn"
SEED_USER_PASSWORD = "User@123456"
SEED_USER_FULL_NAME = "Nguyễn Văn A"

SEED_DEPARTMENT_NAME = "Khoa Công nghệ thông tin"
SEED_MAJOR_CODE = "7480201"
SEED_MAJOR_NAME = "Công nghệ thông tin"

SEED_SUBJECTS = [
    {
        "code": "ITEC2502",
        "name": "Cơ sở dữ liệu",
        "category": SubjectCategory.SPECIALIZED,
        "folder_name": "Cơ sở dữ liệu",
    },
    {
        "code": "ITEC2503",
        "name": "Mạng máy tính",
        "category": SubjectCategory.SPECIALIZED,
        "folder_name": "Mạng máy tính",
    },
    {
        "code": "MISY2501",
        "name": "Cấu trúc dữ liệu và giải thuật",
        "category": SubjectCategory.FOUNDATION,
        "folder_name": "Cấu trúc dữ liệu và giải thuật",
    },
    {
        "code": "ITEC1406",
        "name": "Thiết kế web",
        "category": SubjectCategory.FOUNDATION,
        "folder_name": "Thiết kế web",
    },
]

SEED_ASSETS_DIR = PROJECT_ROOT / "app" / "seed_assets"


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

def calculate_sha256(file_bytes: bytes) -> str:
    """Computes SHA-256 hexadecimal hash string for binary data."""
    return hashlib.sha256(file_bytes).hexdigest()


def determine_resource_type(rel_path_str: str) -> ResourceType:
    """
    Infers ResourceType from folder location:
    - 'lý thuyết' / 'ly thuyet' -> LECTURE
    - 'bài tập' / 'bai tap' / 'thực hành' / 'thuc hanh' -> EXAM
    - Default -> DOCUMENT
    """
    normalized = rel_path_str.lower()
    if "lý thuyết" in normalized or "ly thuyet" in normalized or "theory" in normalized:
        return ResourceType.LECTURE
    if "bài tập" in normalized or "bai tap" in normalized or "thực hành" in normalized or "thuc hanh" in normalized or "exercise" in normalized:
        return ResourceType.EXAM
    return ResourceType.DOCUMENT


def format_title_from_filename(filename: str) -> str:
    """Generates a clean, readable document title from filename."""
    stem = Path(filename).stem
    title = stem.replace("_", " ").replace("-", " ")
    return " ".join(title.split()).strip()


# ─── SEED MODULES ────────────────────────────────────────────────────────────

def seed_users(db: Session) -> tuple[User, User]:
    """Idempotently seeds Admin and Standard User accounts."""
    print("\n" + "-" * 70)
    print(" [1/3] KHỞI TẠO TÀI KHOẢN NGƯỜI DÙNG (USERS & ROLES)")
    print("-" * 70)

    # 1. Admin User (admin@ou.edu.vn)
    admin = db.execute(select(User).where(User.email == SEED_ADMIN_EMAIL)).scalar_one_or_none()
    if admin is None:
        # Check if legacy admin email exists and update
        legacy_admin = db.execute(select(User).where(User.email == getattr(settings, "ADMIN_EMAIL", "admin@gmail.com"))).scalar_one_or_none()
        if legacy_admin is not None:
            legacy_admin.email = SEED_ADMIN_EMAIL
            legacy_admin.full_name = SEED_ADMIN_FULL_NAME
            legacy_admin.password_hash = hash_password(SEED_ADMIN_PASSWORD)
            legacy_admin.role = UserRole.ADMIN
            legacy_admin.is_active = True
            admin = legacy_admin
            db.flush()
            print(f" ✔ Cập nhật Admin: {admin.email} (ID: {admin.id})")
        else:
            admin = User(
                email=SEED_ADMIN_EMAIL,
                full_name=SEED_ADMIN_FULL_NAME,
                password_hash=hash_password(SEED_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.flush()
            print(f" ✔ Tạo mới Admin: {admin.email} (ID: {admin.id})")
    else:
        print(f" ✔ Admin đã tồn tại: {admin.email} (ID: {admin.id})")

    # 2. Demo Standard User (user@ou.edu.vn)
    demo_user = db.execute(select(User).where(User.email == SEED_USER_EMAIL)).scalar_one_or_none()
    if demo_user is None:
        demo_user = User(
            email=SEED_USER_EMAIL,
            full_name=SEED_USER_FULL_NAME,
            password_hash=hash_password(SEED_USER_PASSWORD),
            role=UserRole.USER,
            is_active=True,
        )
        db.add(demo_user)
        db.flush()
        print(f" ✔ Tạo mới Demo User: {demo_user.email} (ID: {demo_user.id})")
    else:
        print(f" ✔ Demo User đã tồn tại: {demo_user.email} (ID: {demo_user.id})")

    db.commit()
    return admin, demo_user


def seed_taxonomy(db: Session) -> tuple[Department, Major, dict[str, Subject]]:
    """Idempotently seeds Department, Major, and 4 Core Subjects."""
    print("\n" + "-" * 70)
    print(" [2/3] KHỞI TẠO CÂY DANH MỤC (KHOA - NGÀNH - MÔN HỌC)")
    print("-" * 70)

    # 1. Department
    dept = db.execute(select(Department).where(Department.name == SEED_DEPARTMENT_NAME)).scalar_one_or_none()
    if dept is None:
        dept = Department(name=SEED_DEPARTMENT_NAME)
        db.add(dept)
        db.flush()
        print(f" ✔ Tạo mới Khoa: {dept.name} (ID: {dept.id})")
    else:
        print(f" ✔ Khoa đã tồn tại: {dept.name} (ID: {dept.id})")

    # 2. Major
    major = db.execute(
        select(Major).where(
            (Major.code == SEED_MAJOR_CODE) | (Major.name == SEED_MAJOR_NAME)
        )
    ).scalar_one_or_none()
    if major is None:
        major = Major(
            code=SEED_MAJOR_CODE,
            name=SEED_MAJOR_NAME,
            department_id=dept.id,
        )
        db.add(major)
        db.flush()
        print(f" ✔ Tạo mới Ngành: [{major.code}] {major.name} (ID: {major.id})")
    else:
        major.code = SEED_MAJOR_CODE
        major.name = SEED_MAJOR_NAME
        major.department_id = dept.id
        db.flush()
        print(f" ✔ Ngành đã xác thực: [{major.code}] {major.name} (ID: {major.id})")

    # 3. Subjects
    subjects_map: dict[str, Subject] = {}
    for sub_info in SEED_SUBJECTS:
        code = sub_info["code"]
        name = sub_info["name"]
        category = sub_info["category"]

        sub = db.execute(
            select(Subject).where(
                (Subject.code == code) | (Subject.name == name)
            )
        ).scalar_one_or_none()
        if sub is None:
            sub = Subject(code=code, name=name)
            db.add(sub)
            db.flush()
            print(f" ✔ Tạo mới Môn học: [{sub.code}] {sub.name} (ID: {sub.id})")
        else:
            sub.code = code
            sub.name = name
            db.flush()
            print(f" ✔ Môn học đã xác thực: [{sub.code}] {sub.name} (ID: {sub.id})")

        # Link in major_subject table with category
        link = db.execute(
            select(major_subject).where(
                major_subject.c.major_id == major.id,
                major_subject.c.subject_id == sub.id,
            )
        ).first()

        if link is None:
            db.execute(
                major_subject.insert().values(
                    major_id=major.id,
                    subject_id=sub.id,
                    category=category,
                )
            )
            print(f"   -> Gắn [{sub.code}] vào Ngành [{major.code}] ({category.value})")
        else:
            db.execute(
                update(major_subject)
                .where(
                    major_subject.c.major_id == major.id,
                    major_subject.c.subject_id == sub.id,
                )
                .values(category=category)
            )

        subjects_map[code] = sub

    db.commit()
    return dept, major, subjects_map


def scan_and_ingest_assets(db: Session, demo_user: User, subjects_map: dict[str, Subject]) -> None:
    """
    Scans backend/app/seed_assets/, uploads files to MinIO, creates Documents & Assets,
    and runs the Ingestion Pipeline with real-time visual terminal progress.
    """
    print("\n" + "-" * 70)
    print(" [3/3] QUÉT THƯ MỤC SEED_ASSETS & INGEST HỌC LIỆU")
    print("-" * 70)

    if not SEED_ASSETS_DIR.exists():
        print(f" ⚠ Thư mục seed_assets không tồn tại: {SEED_ASSETS_DIR}")
        return

    # 1. Pre-collect all eligible files to calculate total N
    folder_to_subject = {
        sub_info["folder_name"]: subjects_map[sub_info["code"]]
        for sub_info in SEED_SUBJECTS
    }

    files_queue: list[tuple[Subject, Path, ResourceType, str]] = []
    for folder_name, subject in folder_to_subject.items():
        subject_folder = SEED_ASSETS_DIR / folder_name
        if not subject_folder.exists():
            continue

        for file_path in sorted(subject_folder.rglob("*")):
            if file_path.is_dir() or file_path.suffix.lower() not in [".pdf", ".docx"]:
                continue
            rel_path = file_path.relative_to(subject_folder)
            res_type = determine_resource_type(str(rel_path))
            files_queue.append((subject, file_path, res_type, folder_name))

    total_files = len(files_queue)
    print(f" 📦 Tổng cộng tìm thấy {total_files} files cần xử lý.\n")

    ingested_count = 0
    skipped_count = 0
    failed_count = 0

    # 2. Iterate and ingest each file with clear visual progress
    for idx, (subject, file_path, resource_type, folder_name) in enumerate(files_queue, start=1):
        filename = file_path.name
        doc_title = format_title_from_filename(filename)

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        file_size = len(file_bytes)
        file_hash = calculate_sha256(file_bytes)
        file_ext = file_path.suffix.lower()
        mime_type = "application/pdf" if file_ext == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        minio_object_path = f"documents/{subject.code.lower()}/{filename}"

        prefix = f" [{idx:02d}/{total_files:02d}] [{subject.code}]"

        # Check existing asset
        existing_asset = db.execute(
            select(Asset)
            .join(Document, Asset.document_id == Document.id)
            .where(
                Document.subject_id == subject.id,
                Asset.file_name == filename,
            )
        ).scalar_one_or_none()

        if existing_asset is not None:
            if existing_asset.ingestion_status == AssetIngestionStatus.COMPLETED:
                print(f"{prefix} ⏭ Bỏ qua (Đã xử lý): {filename} (Số chunks: {existing_asset.chunk_count})")
                skipped_count += 1
                continue
            elif existing_asset.ingestion_status == AssetIngestionStatus.FAILED and existing_asset.ingestion_error == "SCANNED_DOCUMENT_UNSUPPORTED":
                print(f"{prefix} ⏭ Bỏ qua (Tài liệu ảnh scan không chứa text): {filename}")
                skipped_count += 1
                continue
            else:
                print(f"{prefix} 🔄 Đang xử lý lại asset: {filename} (ID: {existing_asset.id})")
                doc = existing_asset.document
                asset = existing_asset
        else:
            # 1. Upload MinIO
            try:
                upload_object(
                    object_path=minio_object_path,
                    data=file_bytes,
                    content_type=mime_type,
                )
            except Exception as e:
                print(f"{prefix} ❌ MinIO Upload thất bại: {filename} ({e})")
                failed_count += 1
                continue

            # 2. Create Document
            doc = Document(
                title=doc_title,
                description=f"Học liệu môn {subject.name} - {doc_title}",
                subject_id=subject.id,
                created_by=demo_user.id,
                resource_type=resource_type,
                status=DocumentStatus.PUBLIC,
            )
            db.add(doc)
            db.flush()

            # 3. Create Asset
            asset = Asset(
                document_id=doc.id,
                uploaded_by=demo_user.id,
                file_name=filename,
                file_path=minio_object_path,
                file_type=mime_type,
                size=file_size,
                file_hash=file_hash,
                ingestion_status=AssetIngestionStatus.PENDING,
            )
            db.add(asset)
            db.flush()

        # Handle DOCX conversion if needed
        if file_ext == ".docx" and asset.conversion_status != AssetConversionStatus.COMPLETED:
            convert_docx_to_pdf_task(asset.id)
            db.refresh(asset)

        # Ingestion Pipeline
        success = ingest_asset(asset.id, db)
        db.refresh(asset)

        if success:
            print(f"{prefix} ✔ Hoàn thành Ingest: {filename} (Số chunks: {asset.chunk_count})")
            ingested_count += 1
        else:
            print(f"{prefix} ⚠ Ingest không thành công: {filename} (Lỗi: {asset.ingestion_error})")
            failed_count += 1

        db.commit()
        time.sleep(settings.GEMINI_RETRIEVAL_EMBED_RETRY_MIN_WAIT)

    print("\n" + "=" * 70)
    print(f" 📊 TỔNG KẾT INGEST: Tổng: {total_files} | Hoàn thành: {ingested_count} | Bỏ qua: {skipped_count} | Lỗi: {failed_count}")
    print("=" * 70)


def seed_demo_workspace(db: Session, demo_user: User, subjects_map: dict[str, Subject]) -> None:
    """
    Seeds a ready-to-use demo Workspace for user@ou.edu.vn with:
    - A Notebook linked to 'Cơ sở dữ liệu' (ITEC2502)
    - Saved documents linked from seeded CSDL documents
    - A Chat session loaded from scripts/seed_demo_csdl.json with real citations & asset_id links
    - An AI Quiz Artifact with 5 multiple-choice questions
    """
    print("\n" + "-" * 70)
    print(" [5/5] TẠO KHÔNG GIAN HỌC TẬP MẪU (WORKSPACE, CHAT & QUIZ ARTIFACT)")
    print("-" * 70)

    demo_json_path = PROJECT_ROOT / "scripts" / "seed_demo_csdl.json"
    if not demo_json_path.exists():
        print(f" ⚠ Không tìm thấy file {demo_json_path}, bỏ qua seed demo workspace.")
        return

    try:
        with open(demo_json_path, "r", encoding="utf-8") as f:
            demo_data = json.load(f)
    except Exception as e:
        print(f" ⚠ Lỗi đọc file {demo_json_path}: {e}")
        return

    # 1. Get Subject 'Database Systems' (ITEC2502)
    csdl_subject = subjects_map.get("ITEC2502")
    if not csdl_subject:
        csdl_subject = db.execute(select(Subject).where(Subject.code == "ITEC2502")).scalar_one_or_none()

    subject_id = csdl_subject.id if csdl_subject else None

    # 2. Query documents for CSDL
    csdl_docs = []
    if csdl_subject:
        csdl_docs = db.execute(
            select(Document).where(Document.subject_id == csdl_subject.id)
        ).scalars().all()

    # 3. Create or get Notebook
    notebook_title = "Ôn tập Cơ sở dữ liệu"
    notebook = db.execute(
        select(Notebook).where(
            Notebook.owner_id == demo_user.id,
            Notebook.title == notebook_title,
        )
    ).scalar_one_or_none()

    if not notebook:
        notebook = Notebook(
            title=notebook_title,
            owner_id=demo_user.id,
            subject_id=subject_id,
        )
        db.add(notebook)
        db.flush()
        print(f" ✔ Tạo Notebook mẫu: '{notebook.title}' (ID: {notebook.id})")
    else:
        print(f" ℹ Notebook đã tồn tại: '{notebook.title}' (ID: {notebook.id})")

    # 4. Link saved documents
    for doc in csdl_docs:
        existing_link = db.execute(
            select(NotebookSavedDocument).where(
                NotebookSavedDocument.notebook_id == notebook.id,
                NotebookSavedDocument.document_id == doc.id,
            )
        ).scalar_one_or_none()
        if not existing_link:
            db.add(NotebookSavedDocument(notebook_id=notebook.id, document_id=doc.id))
            print(f"   + Gắn tài liệu vào Notebook: '{doc.title}' (Doc ID: {doc.id})")

    db.flush()

    # Map assets for citation linking
    assets = db.execute(
        select(Asset).where(
            Asset.document_id.in_([d.id for d in csdl_docs])
        )
    ).scalars().all() if csdl_docs else []

    asset_map = {a.file_name: a for a in assets}
    default_asset = assets[0] if assets else None

    # 5. Create Chat Session and Messages
    chat_data = demo_data.get("chat_session", {})
    session_title = chat_data.get("title", "Thảo luận Chuẩn hóa CSDL & Đại số quan hệ")

    chat_session = db.execute(
        select(NotebookChatSession).where(
            NotebookChatSession.notebook_id == notebook.id,
            NotebookChatSession.user_id == demo_user.id,
            NotebookChatSession.title == session_title,
        )
    ).scalar_one_or_none()

    if not chat_session:
        chat_session = NotebookChatSession(
            notebook_id=notebook.id,
            user_id=demo_user.id,
            title=session_title,
        )
        db.add(chat_session)
        db.flush()
        print(f" ✔ Tạo Phiên trò chuyện AI mẫu: '{chat_session.title}' (ID: {chat_session.id})")

        messages = chat_data.get("messages", [])
        for msg_item in messages:
            role_str = msg_item.get("role", "user").lower()
            role_enum = ChatMessageRole.ASSISTANT if role_str == "assistant" else ChatMessageRole.USER

            raw_citations = msg_item.get("citations")
            processed_citations = None
            if raw_citations:
                processed_citations = []
                for c in raw_citations:
                    c_dict = dict(c)
                    target_asset = asset_map.get(c_dict.get("file_name"), default_asset)
                    if target_asset:
                        c_dict["asset_id"] = target_asset.id
                        c_dict["file_name"] = target_asset.file_name
                    processed_citations.append(c_dict)

            chat_msg = NotebookChatMessage(
                session_id=chat_session.id,
                role=role_enum,
                content=msg_item.get("content", ""),
                citations=processed_citations,
                prompt_tokens=msg_item.get("prompt_tokens"),
                completion_tokens=msg_item.get("completion_tokens"),
            )
            db.add(chat_msg)
        print(f"   + Đã nạp {len(messages)} tin nhắn hỏi-đáp RAG kèm citations.")

    # 6. Create Artifact (Quiz)
    artifact_data = demo_data.get("artifact", {})
    if artifact_data:
        art_title = artifact_data.get("title", "Bộ câu hỏi ôn tập: Chuẩn hóa CSDL & Đại số quan hệ")
        existing_art = db.execute(
            select(NotebookArtifact).where(
                NotebookArtifact.notebook_id == notebook.id,
                NotebookArtifact.title == art_title,
            )
        ).scalar_one_or_none()

        if not existing_art:
            art_type_str = artifact_data.get("artifact_type", "QUIZ").upper()
            try:
                art_type = ArtifactType[art_type_str]
            except KeyError:
                art_type = ArtifactType.QUIZ

            artifact = NotebookArtifact(
                notebook_id=notebook.id,
                user_id=demo_user.id,
                title=art_title,
                artifact_type=art_type,
                content=artifact_data.get("content", {}),
                metadata_=artifact_data.get("metadata", {}),
            )
            db.add(artifact)
            print(f" ✔ Tạo Artifact mẫu ({art_type.value}): '{artifact.title}'")

    db.commit()
    print(" ✔ Hoàn thành khởi tạo không gian học tập mẫu thành công.")


# ─── MAIN RUNNER (CLEAN STATE ARCHITECTURE) ──────────────────────────────────

def clean_minio_bucket(minio_client) -> None:
    """Empty MinIO bucket to ensure clean storage state."""
    bucket_name = settings.MINIO_BUCKET_NAME
    print("\n" + "-" * 70)
    print(" [1/5] LÀM SẠCH OBJECT STORAGE (MINIO BUCKET RESET)")
    print("-" * 70)
    try:
        buckets = [b.name for b in minio_client.list_buckets()]
        if bucket_name in buckets:
            objects = list(minio_client.list_objects(bucket_name, recursive=True))
            if objects:
                for obj in objects:
                    minio_client.remove_object(bucket_name, obj.object_name)
                print(f" ✔ Đã dọn sạch {len(objects)} objects cũ trong bucket '{bucket_name}'.")
            else:
                print(f" ✔ Bucket '{bucket_name}' đang trống sẵn.")
        else:
            minio_client.make_bucket(bucket_name)
            print(f" ✔ Đã tạo mới bucket '{bucket_name}'.")
    except Exception as e:
        print(f" ❌ Lỗi dọn dẹp MinIO: {e}")
        raise


def clean_database_tables(db: Session) -> None:
    """Truncates all business tables to reset database state cleanly."""
    print("\n" + "-" * 70)
    print(" [2/5] LÀM SẠCH CƠ SỞ DỮ LIỆU (POSTGRESQL TRUNCATE CASCADE)")
    print("-" * 70)
    # Ensure all tables exist first
    Base.metadata.create_all(bind=engine)

    truncate_sql = """
    TRUNCATE TABLE 
        users, 
        departments, 
        majors, 
        subjects, 
        major_subject, 
        documents, 
        assets, 
        asset_embeddings, 
        notebooks, 
        notebook_saved_documents, 
        notebook_chat_sessions, 
        notebook_chat_messages, 
        notebook_artifacts, 
        payment_orders 
    RESTART IDENTITY CASCADE;
    """
    try:
        db.execute(text(truncate_sql))
        db.commit()
        print(" ✔ Đã dọn sạch toàn bộ dữ liệu nghiệp vụ (IDs đã được reset về 1).")
    except Exception as e:
        db.rollback()
        print(f" ⚠ Thông báo khi truncate: {e}")


def run_seed(clean_state: bool = True) -> None:
    """Main execution pipeline."""
    print("=" * 70)
    print("   HỆ THỐNG CHIA SẺ HỌC LIỆU - SEED DỮ LIỆU NỀN TẢNG (CLEAN STATE)")
    print("=" * 70)

    # 1. MinIO Connection & Clean Storage
    try:
        minio_client = get_minio_client()
        if clean_state:
            clean_minio_bucket(minio_client)
        else:
            buckets = [b.name for b in minio_client.list_buckets()]
            if settings.MINIO_BUCKET_NAME not in buckets:
                minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
    except Exception as e:
        print(
            f"❌ LỖI KẾT NỐI MINIO ({settings.MINIO_HOST}:{settings.MINIO_API_PORT}).\n"
            f"Vui lòng kiểm tra container MinIO đang chạy. Chi tiết: {e}"
        )
        sys.exit(1)

    # 2. Database Clean & Seeding
    db = SessionLocal()
    try:
        if clean_state:
            clean_database_tables(db)

        print("\n" + "-" * 70)
        print(" [3/5] KHỞI TẠO TÀI KHOẢN HỆ THỐNG & CÂY DANH MỤC")
        print("-" * 70)
        admin, demo_user = seed_users(db)
        dept, major, subjects_map = seed_taxonomy(db)

        print("\n" + "-" * 70)
        print(" [4/5] NẠP HỌC LIỆU MẪU & TẠO CHỈ MỤC TÌM KIẾM VECTOR")
        print("-" * 70)
        scan_and_ingest_assets(db, demo_user, subjects_map)

        # 5. Demo Workspace
        seed_demo_workspace(db, demo_user, subjects_map)

        print("\n" + "=" * 70)
        print("   ✔ TOÀN BỘ DỮ LIỆU VÀ STORAGE ĐÃ ĐỒNG BỘ 100%!")
        print("   Tài khoản Admin : admin@ou.edu.vn / Admin@123456")
        print("   Tài khoản User  : user@ou.edu.vn / User@123456")
        print("   Workspace Mẫu   : 'Ôn tập Cơ sở dữ liệu' (Chat Session & Quiz)")
        print("   Hệ thống sẵn sàng cho nghiệm thu & demo đồ án.")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        logger.exception(f"❌ Lỗi trong quá trình seed dữ liệu: {e}")
        sys.exit(1)
    finally:
        db.close()
        try:
            from app.core.observability import flush_langfuse
            flush_langfuse()
        except Exception:
            pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed clean baseline data for Knowledge Sharing Platform.")
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning MinIO and database before seeding (keep existing data)",
    )
    args = parser.parse_args()
    run_seed(clean_state=not args.no_clean)