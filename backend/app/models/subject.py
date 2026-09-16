from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.major import major_subject

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.major import Major
    from app.models.notebook import Notebook


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationship with Majors via association table
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