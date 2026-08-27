from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import logging

from app.models.asset import Asset
from app.models.document import Document
from app.models.enums import DocumentStatus, AssetConversionStatus
from app.models.notebook import Notebook, NotebookSavedDocument
from app.models.subject import Subject
from app.models.user import User
from app.schemas.notebook import NotebookCreate, NotebookUpdate

logger = logging.getLogger(__name__)

PRESIGNED_URL_EXPIRES_SECONDS = 900


def delete_minio_objects_background(file_paths: list[str]) -> None:
    from app.services.storage_service import delete_object
    for path in file_paths:
        try:
            delete_object(path)
        except Exception as e:
            logger.error(f"Failed to delete object from MinIO: {path}. Error: {e}")


def _get_subject_or_404(db: Session, subject_id: int) -> Subject:
    subject = db.execute(select(Subject).where(Subject.id == subject_id)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )
    return subject


def create_notebook(db: Session, user: User, data: NotebookCreate) -> Notebook:
    if data.subject_id is not None:
        _get_subject_or_404(db, data.subject_id)

    notebook = Notebook(
        title=data.title,
        owner_id=user.id,
        subject_id=data.subject_id,
    )
    db.add(notebook)
    db.commit()
    db.refresh(notebook)

    # Attach dynamic properties for mapping to NotebookRead
    notebook.subject_name = notebook.subject.name if notebook.subject else None
    notebook.source_count = 0
    return notebook


def get_notebooks_by_owner(db: Session, user: User) -> list[Notebook]:
    # subquery for assets count
    assets_count_sub = (
        select(Asset.notebook_id, func.count(Asset.id).label("asset_count"))
        .where(Asset.notebook_id.is_not(None))
        .group_by(Asset.notebook_id)
        .subquery()
    )

    # subquery for saved documents count
    saved_docs_count_sub = (
        select(NotebookSavedDocument.notebook_id, func.count(NotebookSavedDocument.document_id).label("saved_count"))
        .group_by(NotebookSavedDocument.notebook_id)
        .subquery()
    )

    # Main query using outer joins to prevent N+1 queries and handle nullable subject_id
    stmt = (
        select(
            Notebook,
            Subject.name.label("subject_name"),
            func.coalesce(assets_count_sub.c.asset_count, 0).label("asset_count"),
            func.coalesce(saved_docs_count_sub.c.saved_count, 0).label("saved_count"),
        )
        .outerjoin(Subject, Notebook.subject_id == Subject.id)
        .outerjoin(assets_count_sub, Notebook.id == assets_count_sub.c.notebook_id)
        .outerjoin(saved_docs_count_sub, Notebook.id == saved_docs_count_sub.c.notebook_id)
        .where(Notebook.owner_id == user.id)
        .order_by(Notebook.created_at.desc())
    )

    results = db.execute(stmt).all()
    notebooks = []
    for row in results:
        notebook = row.Notebook
        notebook.subject_name = row.subject_name
        notebook.source_count = int(row.asset_count + row.saved_count)
        notebooks.append(notebook)

    return notebooks


def update_notebook(db: Session, user: User, notebook_id: int, data: NotebookUpdate) -> Notebook:
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Update database record
    notebook.title = data.title
    db.commit()
    db.refresh(notebook)

    # Attach dynamic properties for mapping to NotebookRead
    notebook.subject_name = notebook.subject.name if notebook.subject else None
    notebook.source_count = len(notebook.assets) + len(notebook.saved_documents)
    return notebook


def delete_notebook(db: Session, user: User, notebook_id: int, background_tasks: BackgroundTasks) -> None:
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Get asset storage paths (file_path column) before committing deletion to the DB
    file_paths = [asset.file_path for asset in notebook.assets if asset.file_path]

    # Delete notebook (DB & SQLAlchemy cascades will delete assets and saved documents)
    db.delete(notebook)
    db.commit()

    # Trigger background tasks to delete files from MinIO
    if file_paths:
        background_tasks.add_task(delete_minio_objects_background, file_paths)


def get_notebook_source_count(db: Session, notebook_id: int) -> int:
    """
    Helper to count the total sources of a notebook.
    A source is either an Asset or a NotebookSavedDocument.
    """
    asset_count = db.scalar(
        select(func.count(Asset.id)).where(Asset.notebook_id == notebook_id)
    ) or 0
    saved_count = db.scalar(
        select(func.count(NotebookSavedDocument.document_id)).where(NotebookSavedDocument.notebook_id == notebook_id)
    ) or 0
    return int(asset_count + saved_count)


def get_notebook_by_id(db: Session, user: User, notebook_id: int) -> dict:
    """
    Fetch the detailed view of a notebook including its sources and quota status.
    """
    notebook = db.execute(
        select(Notebook).where(Notebook.id == notebook_id)
    ).scalar_one_or_none()

    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Get local assets
    local_assets = db.execute(
        select(Asset).where(Asset.notebook_id == notebook_id)
    ).scalars().all()

    # Get saved documents
    saved_docs = db.execute(
        select(NotebookSavedDocument)
        .where(NotebookSavedDocument.notebook_id == notebook_id)
    ).scalars().all()

    # Combine sources
    sources = []
    for asset in local_assets:
        sources.append({
            "id": asset.id,
            "type": "local",
            "title": asset.file_name,
            "file_type": asset.file_type,
            "size": asset.size,
            "created_at": asset.created_at,
            "conversion_status": asset.conversion_status,
        })

    for sd in saved_docs:
        doc = sd.document
        doc_asset_size = doc.assets[0].size if doc.assets else None
        doc_asset_type = doc.assets[0].file_type if doc.assets else doc.resource_type.value

        sources.append({
            "id": doc.id,
            "type": "saved",
            "title": doc.title,
            "file_type": doc_asset_type,
            "size": doc_asset_size,
            "created_at": sd.created_at,
        })

    # Sort sources by created_at descending (newest first)
    sources.sort(key=lambda s: s["created_at"], reverse=True)

    from app.core.config import settings

    return {
        "id": notebook.id,
        "title": notebook.title,
        "subject_id": notebook.subject_id,
        "subject_name": notebook.subject.name if notebook.subject else None,
        "sources_count": len(sources),
        "max_sources": settings.MAX_SOURCES_PER_NOTEBOOK,
        "sources": sources,
        "created_at": notebook.created_at,
        "updated_at": notebook.updated_at,
    }


def save_document(db: Session, user: User, notebook_id: int, document_id: int) -> NotebookSavedDocument:
    # 1. Notebook existence & ownership validation
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # 2. Document existence & PUBLIC status check
    document = db.execute(select(Document).where(Document.id == document_id)).scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.status != DocumentStatus.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot save document that is not public",
        )

    # 3. Check for duplicates
    existing_link = db.execute(
        select(NotebookSavedDocument).where(
            NotebookSavedDocument.notebook_id == notebook_id,
            NotebookSavedDocument.document_id == document_id,
        )
    ).scalar_one_or_none()
    if existing_link is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document is already saved in this notebook",
        )

    # 4. Check unified sources limit
    from app.core.config import settings
    total_sources = get_notebook_source_count(db, notebook_id)
    if total_sources >= settings.MAX_SOURCES_PER_NOTEBOOK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Notebook source limit reached ({settings.MAX_SOURCES_PER_NOTEBOOK} sources maximum)",
        )

    # 5. Insert association link
    saved_doc = NotebookSavedDocument(
        notebook_id=notebook_id,
        document_id=document_id,
    )
    db.add(saved_doc)
    db.commit()
    db.refresh(saved_doc)
    return saved_doc


def remove_saved_document(db: Session, user: User, notebook_id: int, document_id: int) -> None:
    # 1. Notebook existence & ownership validation
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # 2. Check if link exists
    link = db.execute(
        select(NotebookSavedDocument).where(
            NotebookSavedDocument.notebook_id == notebook_id,
            NotebookSavedDocument.document_id == document_id,
        )
    ).scalar_one_or_none()

    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document is not saved in this notebook",
        )

    db.delete(link)
    db.commit()


def validate_file_content(file_bytes: bytes, file_name: str) -> str:
    import zipfile
    import io
    from app.core.config import settings

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dung lượng tệp vượt quá giới hạn cho phép ({settings.MAX_FILE_SIZE_MB}MB)",
        )

    # Check PDF magic bytes
    if file_bytes.startswith(b"%PDF"):
        return "application/pdf"

    # Check DOCX (ZIP archive containing structural XMLs)
    if file_bytes.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                namelist = zf.namelist()
                if "word/document.xml" in namelist or "[Content_Types].xml" in namelist:
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        except zipfile.BadZipFile:
            pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Định dạng tệp không được hỗ trợ. Chỉ chấp nhận tệp tin PDF hoặc DOCX.",
    )


def upload_notebook_asset(
    db: Session,
    user: User,
    notebook_id: int,
    file_name: str,
    file_bytes: bytes,
    background_tasks: BackgroundTasks,
) -> Asset:
    # 1. Notebook ownership & existence checks
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # 2. Check quota limit using get_notebook_source_count()
    from app.core.config import settings
    current_sources = get_notebook_source_count(db, notebook_id)
    if current_sources >= settings.MAX_SOURCES_PER_NOTEBOOK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Notebook source limit reached ({settings.MAX_SOURCES_PER_NOTEBOOK} sources maximum)",
        )

    # 3. Content-based validate file type and size limit
    content_type = validate_file_content(file_bytes, file_name)

    # 4. Generate unique storage path and upload to MinIO
    import uuid
    import os
    file_ext = os.path.splitext(file_name)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    object_path = f"notebooks/{notebook_id}/{unique_filename}"

    # Perform upload
    from app.services import storage_service
    storage_service.upload_object(
        object_path=object_path,
        data=file_bytes,
        content_type=content_type,
    )

    # 5. Insert Asset database record
    is_docx = content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    conversion_status = AssetConversionStatus.PENDING if is_docx else None

    asset = Asset(
        notebook_id=notebook_id,
        document_id=None,
        file_name=file_name,
        file_path=object_path,
        file_type=content_type,
        size=len(file_bytes),
        conversion_status=conversion_status,
        converted_pdf_path=None,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    if is_docx:
        from app.services.conversion_service import convert_docx_to_pdf_task
        background_tasks.add_task(convert_docx_to_pdf_task, asset.id)
    else:
        from app.services.ingestion_service import ingest_asset_background_task
        background_tasks.add_task(ingest_asset_background_task, asset.id)

    return asset


def delete_notebook_asset(
    db: Session,
    user: User,
    notebook_id: int,
    asset_id: int,
    background_tasks: BackgroundTasks,
) -> None:
    # 1. Notebook ownership & existence checks
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # 2. Check if asset exists and belongs to this notebook
    asset = db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.notebook_id == notebook_id,
        )
    ).scalar_one_or_none()

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found in this notebook",
        )

    # Get path for background deletion
    file_path = asset.file_path

    # Delete from postgres first
    db.delete(asset)
    db.commit()

    # Deletion from storage (best-effort async background task)
    if file_path:
        background_tasks.add_task(delete_minio_objects_background, [file_path])


def get_notebook_asset_download_url(
    db: Session,
    user: User,
    notebook_id: int,
    asset_id: int,
) -> tuple[str, str]:
    # 1. Notebook ownership & existence checks
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # 2. Get asset
    asset = db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.notebook_id == notebook_id,
        )
    ).scalar_one_or_none()

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found in this notebook",
        )

    import os
    from app.services import storage_service

    if asset.converted_pdf_path:
        object_path = asset.converted_pdf_path
        base_name, _ = os.path.splitext(asset.file_name)
        file_name = f"{base_name}.pdf"
    else:
        object_path = asset.file_path
        file_name = asset.file_name

    download_url = storage_service.get_presigned_download_url(
        object_path=object_path,
        expires_seconds=PRESIGNED_URL_EXPIRES_SECONDS,
    )
    return download_url, file_name


def get_scoped_asset_ids(db: Session, notebook_id: int) -> list[int]:
    """
    Retrieves all Completed Asset IDs scoped to this notebook:
    1. Assets uploaded directly to the notebook.
    2. Assets belonging to documents saved in the notebook.
    Only returns assets with ingestion_status == COMPLETED.
    """
    from app.models.asset import Asset
    from app.models.notebook import NotebookSavedDocument
    from app.models.enums import AssetIngestionStatus
    from sqlalchemy import select

    # Direct assets
    direct_ids = db.execute(
        select(Asset.id).where(
            Asset.notebook_id == notebook_id,
            Asset.ingestion_status == AssetIngestionStatus.COMPLETED,
        )
    ).scalars().all()

    # Saved document asset ids
    saved_doc_ids = db.execute(
        select(NotebookSavedDocument.document_id).where(
            NotebookSavedDocument.notebook_id == notebook_id
        )
    ).scalars().all()

    saved_ids = []
    if saved_doc_ids:
        saved_ids = db.execute(
            select(Asset.id).where(
                Asset.document_id.in_(saved_doc_ids),
                Asset.ingestion_status == AssetIngestionStatus.COMPLETED,
            )
        ).scalars().all()

    # Combine and de-duplicate
    return list(set(direct_ids) | set(saved_ids))


