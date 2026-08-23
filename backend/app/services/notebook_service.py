from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import logging

from app.models.asset import Asset
from app.models.notebook import Notebook, NotebookSavedDocument
from app.models.subject import Subject
from app.models.user import User
from app.schemas.notebook import NotebookCreate, NotebookUpdate

logger = logging.getLogger(__name__)


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

