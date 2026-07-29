from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )