from fastapi import APIRouter, BackgroundTasks, Depends, status, File, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.asset import AssetResponse, AssetIngestionStatusResponse
from app.schemas.document import AssetDownloadResponse
from app.schemas.notebook import (
    NotebookCreate,
    NotebookRead,
    NotebookUpdate,
    NotebookDetailRead,
    NotebookSavedDocumentCreate,
    NotebookSavedDocumentRead,
)
from app.services import notebook_service

router = APIRouter(prefix="/notebooks", tags=["Notebooks"])


@router.post("/", response_model=NotebookRead, status_code=status.HTTP_201_CREATED)
def create_notebook(
    data: NotebookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.create_notebook(db, current_user, data)


@router.get("/me", response_model=list[NotebookRead])
def list_my_notebooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.get_notebooks_by_owner(db, current_user)


@router.get("/{notebook_id}", response_model=NotebookDetailRead)
def get_notebook_detail(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.get_notebook_by_id(db, current_user, notebook_id)


@router.patch("/{notebook_id}", response_model=NotebookRead)
def rename_notebook(
    notebook_id: int,
    data: NotebookUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.update_notebook(db, current_user, notebook_id, data)


@router.delete("/{notebook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notebook(
    notebook_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notebook_service.delete_notebook(db, current_user, notebook_id, background_tasks)


@router.post("/{notebook_id}/saved-documents", response_model=NotebookSavedDocumentRead, status_code=status.HTTP_201_CREATED)
def save_document(
    notebook_id: int,
    data: NotebookSavedDocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.save_document(db, current_user, notebook_id, data.document_id)


@router.delete("/{notebook_id}/saved-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_document(
    notebook_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notebook_service.remove_saved_document(db, current_user, notebook_id, document_id)


@router.post("/{notebook_id}/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    notebook_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    return notebook_service.upload_notebook_asset(
        db,
        current_user,
        notebook_id,
        file.filename or "unnamed_file",
        file_bytes,
        background_tasks,
    )


@router.delete("/{notebook_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    notebook_id: int,
    asset_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notebook_service.delete_notebook_asset(db, current_user, notebook_id, asset_id, background_tasks)


@router.get("/{notebook_id}/assets/{asset_id}/download", response_model=AssetDownloadResponse)
def get_download_url(
    notebook_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    download_url, file_name = notebook_service.get_notebook_asset_download_url(db, current_user, notebook_id, asset_id)
    return AssetDownloadResponse(
        download_url=download_url,
        file_name=file_name,
        expires_in_seconds=notebook_service.PRESIGNED_URL_EXPIRES_SECONDS,
    )


@router.get("/{notebook_id}/assets/{asset_id}/status", response_model=AssetIngestionStatusResponse)
def get_asset_ingestion_status(
    notebook_id: int,
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.models.notebook import Notebook
    from app.models.asset import Asset
    from fastapi import HTTPException
    from sqlalchemy import select

    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

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

    return AssetIngestionStatusResponse(
        asset_id=asset.id,
        file_name=asset.file_name,
        ingestion_status=asset.ingestion_status,
        chunk_count=asset.chunk_count,
        ingestion_error=asset.ingestion_error,
    )



