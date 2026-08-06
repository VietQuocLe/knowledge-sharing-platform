from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.major import major_subject  # Nhập bảng trung gian

if TYPE_CHECKING:
    from app.models.learning_resource import LearningResource
    from app.models.major import Major
    from app.models.department import Department  # Thêm dòng này


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # --- THÊM KHÓA NGOẠI DEPARTMENT_ID ---
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # --- THÊM RELATIONSHIP TỚI DEPARTMENT ---
    department: Mapped["Department"] = relationship(back_populates="subjects")

    # Nối với Major (Ngành) thông qua bảng trung gian
    majors: Mapped[list["Major"]] = relationship(
        secondary=major_subject,
        back_populates="subjects",
    )

    resources: Mapped[list["LearningResource"]] = relationship(
        back_populates="subject"
    )