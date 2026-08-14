from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.major import Major
from app.schemas.major import MajorCreate, MajorUpdate


def get_all(db: Session, *, department_id: int | None = None) -> list[Major]:
    query = select(Major).order_by(Major.id)
    if department_id is not None:
        _get_department_or_404(db, department_id)
        query = query.where(Major.department_id == department_id)
    result = db.execute(query)
    return list(result.scalars().all())


def get_by_id(db: Session, major_id: int) -> Major:
    major = db.execute(select(Major).where(Major.id == major_id)).scalar_one_or_none()
    if major is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Major not found")
    return major


def _get_department_or_404(db: Session, department_id: int) -> Department:
    department = db.execute(
        select(Department).where(Department.id == department_id)
    ).scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


def create(db: Session, data: MajorCreate) -> Major:
    _get_department_or_404(db, data.department_id)

    existing = db.execute(
        select(Major).where((Major.code == data.code) | (Major.name == data.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Major already exists")

    major = Major(
        code=data.code,
        name=data.name,
        department_id=data.department_id,
    )
    db.add(major)
    db.commit()
    db.refresh(major)
    return major


def update(db: Session, major_id: int, data: MajorUpdate) -> Major:
    major = get_by_id(db, major_id)

    if data.department_id is not None:
        _get_department_or_404(db, data.department_id)
        major.department_id = data.department_id

    if data.code is not None and data.code != major.code:
        existing = db.execute(
            select(Major).where(Major.code == data.code, Major.id != major_id)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Major already exists")
        major.code = data.code

    if data.name is not None and data.name != major.name:
        existing = db.execute(
            select(Major).where(Major.name == data.name, Major.id != major_id)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Major already exists")
        major.name = data.name

    db.commit()
    db.refresh(major)
    return major


def delete(db: Session, major_id: int) -> None:
    major = get_by_id(db, major_id)
    db.delete(major)
    db.commit()