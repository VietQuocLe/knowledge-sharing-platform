from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DocumentStatus, ResourceType

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.notebook import NotebookSavedDocument
    from app.models.subject import Subject
    from app.models.user import User


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        default=None,
    )

    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType, name="resource_type"),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.PUBLIC,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    creator: Mapped["User | None"] = relationship(back_populates="documents")

    subject: Mapped["Subject"] = relationship(back_populates="documents")

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="Asset.id",
    )

    saved_in_notebooks: Mapped[list["NotebookSavedDocument"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
