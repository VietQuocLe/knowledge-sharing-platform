from fastapi import APIRouter, BackgroundTasks, Depends, status, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse
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
from app.schemas.notebook_chat import (
    NotebookChatSessionCreate,
    NotebookChatSessionRead,
    NotebookChatSessionUpdate,
    NotebookChatMessageCreate,
    NotebookChatMessageRead,
)
from app.services import notebook_chat_service
from app.services import artifact_service
from app.schemas.artifact import (
    QuizGenerateRequest,
    ArtifactSummaryResponse,
    ArtifactDetailResponse,
)

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


# --- Chat Sessions & Messages endpoints ---

@router.post("/{notebook_id}/sessions", response_model=NotebookChatSessionRead, status_code=status.HTTP_201_CREATED)
def create_session(
    notebook_id: int,
    data: NotebookChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_chat_service.create_chat_session(db, notebook_id, current_user, data)


@router.get("/{notebook_id}/sessions", response_model=list[NotebookChatSessionRead])
def list_sessions(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_chat_service.list_sessions_by_notebook(db, notebook_id, current_user)


@router.get("/{notebook_id}/sessions/{session_id}/messages", response_model=list[NotebookChatMessageRead])
def get_messages(
    notebook_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_chat_service.get_session_messages(db, notebook_id, session_id, current_user)


@router.patch("/{notebook_id}/sessions/{session_id}", response_model=NotebookChatSessionRead)
def rename_session(
    notebook_id: int,
    session_id: int,
    data: NotebookChatSessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_chat_service.rename_chat_session(db, notebook_id, session_id, current_user, data)


@router.delete("/{notebook_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    notebook_id: int,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notebook_chat_service.delete_chat_session(db, notebook_id, session_id, current_user)


@router.post("/{notebook_id}/sessions/{session_id}/messages", response_model=NotebookChatMessageRead, status_code=status.HTTP_201_CREATED)
def create_message(
    notebook_id: int,
    session_id: int,
    data: NotebookChatMessageCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Direct message creation is disabled. Use the chat streaming endpoint instead.",
    )


@router.post("/{notebook_id}/sessions/{session_id}/chat")
async def chat_stream_endpoint(
    notebook_id: int,
    session_id: int,
    data: NotebookChatMessageCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG Chat endpoint returning Server-Sent Events (SSE).
    """
    # 1. Validation & Ownership Guard
    notebook_chat_service.validate_notebook_and_session(db, notebook_id, current_user.id, session_id)
    
    # 2. Concurrency Lock check
    lock = notebook_chat_service.get_session_lock(session_id)
    if lock.locked():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phiên trò chuyện đang bận xử lý một yêu cầu khác.",
        )
    
    # 3. Acquire lock without any await statements beforehand to avoid race
    await lock.acquire()

    # 4. Return StreamingResponse with lock release block
    async def event_generator():
        try:
            async for sse_event in notebook_chat_service.stream_chat_response(
                db, notebook_id, session_id, current_user, data.content, request, background_tasks
            ):
                yield sse_event
        finally:
            lock.release()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# --- Quiz / Artifacts endpoints ---

@router.post("/{notebook_id}/artifacts/generate", response_model=ArtifactDetailResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    notebook_id: int,
    payload: QuizGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return artifact_service.generate_quiz_mock(db, notebook_id, current_user.id, payload)


@router.get("/{notebook_id}/artifacts", response_model=list[ArtifactSummaryResponse])
def list_artifacts(
    notebook_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return artifact_service.list_notebook_artifacts(db, notebook_id, current_user.id)


@router.get("/{notebook_id}/artifacts/{artifact_id}", response_model=ArtifactDetailResponse)
def get_artifact_detail(
    notebook_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return artifact_service.get_notebook_artifact_detail(db, notebook_id, artifact_id, current_user.id)


@router.delete("/{notebook_id}/artifacts/{artifact_id}", response_model=dict)
def delete_artifact(
    notebook_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    artifact_service.delete_notebook_artifact(db, notebook_id, artifact_id, current_user.id)
    return {"status": "deleted"}




