import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

logger = logging.getLogger(__name__)


def ensure_admin_exists(db: Session) -> None:
    existing = db.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    ).scalar_one_or_none()

    if existing:
        logger.info("Default admin already exists.")
        return

    admin = User(
        email=settings.ADMIN_EMAIL,
        full_name=settings.ADMIN_FULL_NAME,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
    )

    db.add(admin)
    db.commit()

    logger.info("Default admin created.")


def initialize_system(db: Session) -> None:
    """
    Khởi tạo dữ liệu mặc định của hệ thống.
    """
    ensure_admin_exists(db)