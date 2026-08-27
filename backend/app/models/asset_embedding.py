from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func, Computed
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.asset import Asset


class AssetEmbedding(Base):
    __tablename__ = "asset_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[Any] = mapped_column(Vector(768), nullable=True)

    tsv_content: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('simple', immutable_unaccent(content))", persisted=True),
        nullable=True,
    )

    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    asset: Mapped["Asset"] = relationship(back_populates="embeddings")

    # Table constraints and indexes
    __table_args__ = (
        UniqueConstraint("asset_id", "chunk_index", name="uq_asset_embeddings_asset_chunk"),
        Index(
            "idx_asset_embeddings_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_with={"m": 16, "ef_construction": 64},
        ),
        Index(
            "idx_asset_embeddings_tsv_content",
            "tsv_content",
            postgresql_using="gin",
        ),
    )
