from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AssetConversionStatus, AssetIngestionStatus

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.notebook import Notebook
    from app.models.asset_embedding import AssetEmbedding
    from app.models.user import User


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (
        CheckConstraint(
            "(document_id IS NOT NULL AND notebook_id IS NULL) "
            "OR (document_id IS NULL AND notebook_id IS NOT NULL)",
            name="ck_assets_document_xor_notebook",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    notebook_id: Mapped[int | None] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)

    file_type: Mapped[str] = mapped_column(String(100), nullable=False)

    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    converted_pdf_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    conversion_status: Mapped[AssetConversionStatus | None] = mapped_column(
        SQLEnum(AssetConversionStatus, name="asset_conversion_status"),
        nullable=True,
    )

    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    ingestion_status: Mapped[AssetIngestionStatus] = mapped_column(
        SQLEnum(AssetIngestionStatus, name="asset_ingestion_status"),
        default=AssetIngestionStatus.PENDING,
        nullable=False,
    )

    ingestion_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    uploader: Mapped["User | None"] = relationship()

    document: Mapped["Document | None"] = relationship(back_populates="assets")

    notebook: Mapped["Notebook | None"] = relationship(back_populates="assets")

    embeddings: Mapped[list["AssetEmbedding"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )

