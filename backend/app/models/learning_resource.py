from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    ResourceStatus,
    ResourceType,
    VisibilityEnum,
)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    file_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType),
        nullable=False,
    )

    visibility: Mapped[VisibilityEnum] = mapped_column(
        Enum(VisibilityEnum),
        default=VisibilityEnum.PRIVATE,
        nullable=False,
    )

    status: Mapped[ResourceStatus] = mapped_column(
        Enum(ResourceStatus),
        default=ResourceStatus.PROCESSING,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    owner: Mapped["User"] = relationship(back_populates="resources")

    subject: Mapped["Subject"] = relationship(back_populates="resources")