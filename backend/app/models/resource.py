from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ResourceType, VisibilityEnum, ResourceStatus

if TYPE_CHECKING:
    from app.models.subject import Subject
    from app.models.user import User


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)

    description: Mapped[str | None] = mapped_column(Text)

    resource_type: Mapped[ResourceType] = mapped_column(
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        default=dict,
        nullable=False,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    owner: Mapped["User"] = relationship(back_populates="resources")

    subject: Mapped[Optional["Subject"]] = relationship(back_populates="resources")

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="resource",
        cascade="all, delete-orphan",
        order_by="Asset.id",
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    file_type: Mapped[str] = mapped_column(String(100), nullable=False)

    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    resource: Mapped[Resource] = relationship(back_populates="assets")