from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ArtifactType

if TYPE_CHECKING:
    from app.models.notebook import Notebook
    from app.models.user import User


class NotebookArtifact(Base):
    __tablename__ = "notebook_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    artifact_type: Mapped[ArtifactType] = mapped_column(
        SQLEnum(ArtifactType, name="artifact_type"),
        default=ArtifactType.QUIZ,
        nullable=False
    )
    
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    notebook: Mapped["Notebook"] = relationship("Notebook", back_populates="artifacts")
    user: Mapped["User"] = relationship("User")
