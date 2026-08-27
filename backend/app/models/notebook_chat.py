from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.notebook import Notebook
    from app.models.user import User


class NotebookChatSession(Base):
    __tablename__ = "notebook_chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        default="Phiên trò chuyện mới",
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

    notebook: Mapped["Notebook"] = relationship(back_populates="chat_sessions")
    user: Mapped["User"] = relationship()
    
    messages: Mapped[list["NotebookChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="NotebookChatMessage.created_at.asc()",
    )


class NotebookChatMessage(Base):
    __tablename__ = "notebook_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    session_id: Mapped[int] = mapped_column(
        ForeignKey("notebook_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    
    content: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    
    citations: Mapped[Any | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    condensed_query: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["NotebookChatSession"] = relationship(back_populates="messages")
