from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="subjects")

    resources: Mapped[list["LearningResource"]] = relationship(
        back_populates="subject"
    )