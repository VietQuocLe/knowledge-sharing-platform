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