from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.major import Major
    from app.models.subject import Subject  # Thêm dòng này


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    majors: Mapped[list["Major"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )
    
    # --- THÊM RELATIONSHIP TỚI SUBJECT ---
    # Không dùng cascade delete ở đây để đảm bảo an toàn dữ liệu (RESTRICT delete)
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="department"
    )