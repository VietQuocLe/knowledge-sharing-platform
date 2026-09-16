from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.artifact import NotebookArtifact
from app.models.enums import SubscriptionTier
from app.models.user import User
from app.schemas.auth import UserQuotas


def get_effective_user_tier(db: Session, user: User) -> SubscriptionTier:
    """
    Checks and executes lazy downgrade if user's PRO plan is expired.
    Operates on-demand without requiring a background cron job.
    """
    if user.tier == SubscriptionTier.PRO:
        now_utc = datetime.now(timezone.utc)
        expires_at = user.pro_expires_at
        if expires_at is not None:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            else:
                expires_at = expires_at.astimezone(timezone.utc)

            if expires_at < now_utc:
                # Expired -> Lazy downgrade to FREE
                user.tier = SubscriptionTier.FREE
                db.add(user)
                db.commit()
                db.refresh(user)

    return user.tier


def get_user_quotas(tier: SubscriptionTier) -> UserQuotas:
    """
    Single Source of Truth: returns source and artifact quotas by subscription tier.
    """
    if tier == SubscriptionTier.PRO:
        return UserQuotas(
            max_sources=settings.PRO_MAX_SOURCES,
            max_artifacts=settings.PRO_MAX_ARTIFACTS,
        )
    return UserQuotas(
        max_sources=settings.FREE_MAX_SOURCES,
        max_artifacts=settings.FREE_MAX_ARTIFACTS,
    )


def check_sources_quota(db: Session, user: User, notebook_id: int) -> None:
    """
    Check sources quota on new document addition (Soft-cap Policy).
    Never deletes or hides existing documents. Only blocks addition if current >= max_quota.
    """
    from app.services.notebook_service import get_notebook_source_count

    effective_tier = get_effective_user_tier(db, user)
    quotas = get_user_quotas(effective_tier)
    current_sources = get_notebook_source_count(db, notebook_id)

    if current_sources >= quotas.max_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Bạn đang sử dụng {current_sources}/{quotas.max_sources} nguồn "
                f"(đạt hoặc vượt hạn mức gói {effective_tier.value}). "
                f"Vui lòng xóa bớt tài liệu hoặc gia hạn/nâng cấp gói Pro để tiếp tục thêm mới."
            ),
        )


def check_artifacts_quota(db: Session, user: User, notebook_id: int) -> None:
    """
    Check AI artifacts quota on new generation (Soft-cap Policy).
    Never deletes or hides existing artifacts. Only blocks creation if current >= max_quota.
    """
    effective_tier = get_effective_user_tier(db, user)
    quotas = get_user_quotas(effective_tier)

    count_stmt = (
        select(func.count())
        .select_from(NotebookArtifact)
        .where(NotebookArtifact.notebook_id == notebook_id)
    )
    current_count = db.execute(count_stmt).scalar() or 0

    if current_count >= quotas.max_artifacts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Notebook đã đạt giới hạn tối đa {current_count}/{quotas.max_artifacts} bài tập "
                f"(hạn mức gói {effective_tier.value}). "
                f"Vui lòng xóa bớt bài tập cũ hoặc gia hạn/nâng cấp gói Pro để tạo thêm."
            ),
        )

