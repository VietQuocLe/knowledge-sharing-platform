from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.major import Major
from app.models.subject import Subject
from app.schemas.department import DepartmentCreate, DepartmentUpdate


def get_all(db: Session) -> list[Department]:
    result = db.execute(select(Department).order_by(Department.id))
    return list(result.scalars().all())


def get_by_id(db: Session, department_id: int) -> Department:
    department = db.execute(
        select(Department).where(Department.id == department_id)
    ).scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


def create(db: Session, data: DepartmentCreate) -> Department:
    existing = db.execute(
        select(Department).where(Department.name == data.name)
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")

    department = Department(name=data.name)
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def update(db: Session, department_id: int, data: DepartmentUpdate) -> Department:
    department = get_by_id(db, department_id)

    if data.name is not None and data.name != department.name:
        existing = db.execute(
            select(Department).where(Department.name == data.name, Department.id != department_id)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")
        department.name = data.name

    db.commit()
    db.refresh(department)
    return department


def delete(db: Session, department_id: int) -> None:
    department = get_by_id(db, department_id)

    major_exists = db.execute(
        select(Major.id).where(Major.department_id == department_id).limit(1)
    ).scalar_one_or_none()
    subject_exists = db.execute(
        select(Subject.id)
        .join(Subject.majors)
        .where(Major.department_id == department_id)
        .limit(1)
    ).scalar_one_or_none()
    if major_exists is not None or subject_exists is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with associated majors/subjects",
        )

    db.delete(department)
    db.commit()