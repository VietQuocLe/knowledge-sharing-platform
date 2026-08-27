from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.document import Document
    from app.models.subject import Subject
    from app.models.user import User
    from app.models.notebook_chat import NotebookChatSession
    from app.models.artifact import NotebookArtifact


class Notebook(Base):
    __tablename__ = "notebooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(back_populates="notebooks")

    subject: Mapped["Subject | None"] = relationship(back_populates="notebooks")

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="notebook",
        cascade="all, delete-orphan",
        order_by="Asset.id",
    )

    saved_documents: Mapped[list["NotebookSavedDocument"]] = relationship(
        back_populates="notebook",
        cascade="all, delete-orphan",
    )

    chat_sessions: Mapped[list["NotebookChatSession"]] = relationship(
        back_populates="notebook",
        cascade="all, delete-orphan",
    )

    artifacts: Mapped[list["NotebookArtifact"]] = relationship(
        back_populates="notebook",
        cascade="all, delete-orphan",
    )


class NotebookSavedDocument(Base):
    __tablename__ = "notebook_saved_documents"
    __table_args__ = (
        UniqueConstraint("notebook_id", "document_id", name="uq_notebook_saved_documents"),
    )

    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        primary_key=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    notebook: Mapped["Notebook"] = relationship(back_populates="saved_documents")

    document: Mapped["Document"] = relationship(back_populates="saved_in_notebooks")
