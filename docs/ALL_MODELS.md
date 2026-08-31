# artifact.py
```python
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

```

# asset.py
```python
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


```

# asset_embedding.py
```python
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

    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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

```

# base.py
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

# department.py
```python
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.major import Major


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    majors: Mapped[list["Major"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
```

# document.py
```python
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

```

# enums.py
```python
from enum import Enum


class UserRole(str, Enum):
    USER = "USER"
    PREMIUM_USER = "PREMIUM_USER"
    ADMIN = "ADMIN"


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ResourceType(str, Enum):
    EXAM = "EXAM"
    SLIDE = "SLIDE"
    DOCUMENT = "DOCUMENT"
    LECTURE = "LECTURE"
    REFERENCE = "REFERENCE"
    SYLLABUS = "SYLLABUS"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    LINK = "LINK"
    AI_ARTIFACT = "AI_ARTIFACT"


class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLIC = "PUBLIC"
    DELETED = "DELETED"


class SubjectCategory(str, Enum):
    GENERAL = "GENERAL"
    FOUNDATION = "FOUNDATION"
    SPECIALIZED = "SPECIALIZED"
    ELECTIVE_CAPSTONE = "ELECTIVE_CAPSTONE"


class AssetConversionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AssetIngestionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ArtifactType(str, Enum):
    QUIZ = "QUIZ"
    FLASHCARD = "FLASHCARD"
    SUMMARY = "SUMMARY"




```

# major.py
```python
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import SubjectCategory

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.subject import Subject

# Bảng trung gian giải quyết bài toán: 1 môn đại cương thuộc nhiều ngành
major_subject = Table(
    "major_subject",
    Base.metadata,
    Column("major_id", Integer, ForeignKey("majors.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
    Column("category", Enum(SubjectCategory, name="subject_category"), nullable=False, default=SubjectCategory.GENERAL, server_default='GENERAL'),
)

class Major(Base):
    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # Nối ngược lại Department (Khoa)
    department: Mapped["Department"] = relationship(back_populates="majors")

    # Nối với Subject (Môn học) thông qua bảng trung gian
    subjects: Mapped[list["Subject"]] = relationship(
        secondary=major_subject,
        back_populates="majors",
    )
```

# notebook.py
```python
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
        index=True,
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

```

# notebook_chat.py
```python
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ChatMessageRole

if TYPE_CHECKING:
    from app.models.notebook import Notebook
    from app.models.user import User


class NotebookChatSession(Base):
    __tablename__ = "notebook_chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
        index=True,
    )
    
    role: Mapped[ChatMessageRole] = mapped_column(
        SQLEnum(ChatMessageRole, name="chat_message_role"),
        default=ChatMessageRole.USER,
        nullable=False,
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    citations: Mapped[Any | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    condensed_query: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["NotebookChatSession"] = relationship(back_populates="messages")

```

# subject.py
```python
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.major import major_subject  # Nhập bảng trung gian

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.major import Major
    from app.models.notebook import Notebook


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Nối với Major (Ngành) thông qua bảng trung gian
    majors: Mapped[list["Major"]] = relationship(
        secondary=major_subject,
        back_populates="subjects",
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="subject",
    )

    notebooks: Mapped[list["Notebook"]] = relationship(
        back_populates="subject",
    )
```

# user.py
```python
from __future__ import annotations

from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.notebook import Notebook


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    password_hash: Mapped[str | None] = mapped_column(String(255))

    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    documents: Mapped[list["Document"]] = relationship(
        back_populates="creator",
    )

    notebooks: Mapped[list["Notebook"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
```

# __init__.py
```python
from .base import Base
from .user import User
from .department import Department
from .major import Major
from .subject import Subject
from .document import Document
from .notebook import Notebook, NotebookSavedDocument
from .asset import Asset
from .asset_embedding import AssetEmbedding
from .notebook_chat import NotebookChatSession, NotebookChatMessage
from .artifact import NotebookArtifact

__all__ = [
    "Base",
    "User",
    "Department",
    "Major",
    "Subject",
    "Document",
    "Notebook",
    "NotebookSavedDocument",
    "Asset",
    "AssetEmbedding",
    "NotebookChatSession",
    "NotebookChatMessage",
    "NotebookArtifact",
]


```


