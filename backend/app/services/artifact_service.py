from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, defer

from app.models.artifact import NotebookArtifact
from app.models.notebook import Notebook, NotebookSavedDocument
from app.models.asset import Asset
from app.models.enums import AssetIngestionStatus, ArtifactType
from app.schemas.artifact import QuizGenerateRequest, QuizQuestion, QuizContentPayload


def generate_quiz_mock(db: Session, notebook_id: int, user_id: int, payload: QuizGenerateRequest) -> NotebookArtifact:
    # Bước 1 (Ownership Guard)
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Bước 2 (Cooldown 15s Guard)
    stmt = (
        select(NotebookArtifact)
        .where(NotebookArtifact.user_id == user_id)
        .order_by(NotebookArtifact.created_at.desc())
        .limit(1)
    )
    last_artifact = db.execute(stmt).scalar_one_or_none()
    if last_artifact:
        now_utc = datetime.now(timezone.utc)
        last_created = last_artifact.created_at
        if last_created.tzinfo is None:
            last_created = last_created.replace(tzinfo=timezone.utc)
        else:
            last_created = last_created.astimezone(timezone.utc)

        diff = (now_utc - last_created).total_seconds()
        if diff < 15:
            remaining = int(15 - diff)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Thao tác quá nhanh. Vui lòng thử lại sau {remaining} giây.",
            )

    # Bước 3 (Quota Limit Guard)
    count_stmt = select(func.count()).select_from(NotebookArtifact).where(NotebookArtifact.notebook_id == notebook_id)
    cnt = db.execute(count_stmt).scalar() or 0
    if cnt >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notebook đã đạt giới hạn tối đa 20 bài tập",
        )

    # Bước 4 (All-or-Nothing Asset Check)
    asset_stmt = select(Asset).where(
        Asset.id.in_(payload.selected_asset_ids),
        or_(
            Asset.notebook_id == notebook_id,
            Asset.document_id.in_(
                select(NotebookSavedDocument.document_id).where(
                    NotebookSavedDocument.notebook_id == notebook_id
                )
            )
        )
    )
    assets = db.execute(asset_stmt).scalars().all()

    # Phải tìm thấy tất cả ID được chọn
    if len(assets) != len(set(payload.selected_asset_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Một số tài liệu được chọn không hợp lệ hoặc không thuộc Notebook này",
        )

    # Tất cả phải COMPLETED
    if not all(asset.ingestion_status == AssetIngestionStatus.COMPLETED for asset in assets):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tất cả tài liệu được tuyển chọn phải được xử lý thành công để tạo bài tập",
        )

    # Bước 5 (RAG Generator)
    from app.services.quiz_service import extract_context_from_assets, _call_gemini_with_retry

    context_text = extract_context_from_assets(db, payload.selected_asset_ids)
    quiz_payload = _call_gemini_with_retry(context_text, payload.num_questions)

    title = (quiz_payload.title or "Bộ câu hỏi trắc nghiệm")[:255]

    db_artifact = NotebookArtifact(
        notebook_id=notebook_id,
        user_id=user_id,
        title=title,
        artifact_type=ArtifactType.QUIZ,
        content=quiz_payload.model_dump(),
        metadata_={
            "selected_asset_ids": payload.selected_asset_ids,
            "num_questions": len(quiz_payload.questions),
        }
    )

    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)

    return db_artifact


def list_notebook_artifacts(db: Session, notebook_id: int, user_id: int) -> list[NotebookArtifact]:
    # Kiểm tra quyền truy cập Notebook
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Query loại bỏ content JSONB để tối ưu I/O, sắp xếp created_at DESC
    stmt = (
        select(NotebookArtifact)
        .where(NotebookArtifact.notebook_id == notebook_id)
        .order_by(NotebookArtifact.created_at.desc())
        .options(defer(NotebookArtifact.content))
    )
    return list(db.execute(stmt).scalars().all())


def get_notebook_artifact_detail(db: Session, notebook_id: int, artifact_id: int, user_id: int) -> NotebookArtifact:
    # Kiểm tra quyền truy cập Notebook
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Query chi tiết artifact
    stmt = select(NotebookArtifact).where(
        NotebookArtifact.id == artifact_id,
        NotebookArtifact.notebook_id == notebook_id
    )
    artifact = db.execute(stmt).scalar_one_or_none()
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found in this notebook",
        )

    return artifact


def delete_notebook_artifact(db: Session, notebook_id: int, artifact_id: int, user_id: int) -> None:
    # Kiểm tra quyền truy cập Notebook
    notebook = db.execute(select(Notebook).where(Notebook.id == notebook_id)).scalar_one_or_none()
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )
    if notebook.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access/modify this notebook",
        )

    # Query artifact
    stmt = select(NotebookArtifact).where(
        NotebookArtifact.id == artifact_id,
        NotebookArtifact.notebook_id == notebook_id
    )
    artifact = db.execute(stmt).scalar_one_or_none()
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found in this notebook",
        )

    db.delete(artifact)
    db.commit()
