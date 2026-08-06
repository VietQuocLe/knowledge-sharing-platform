from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.major import Major
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


def get_all(db: Session) -> list[Subject]:
    result = db.execute(select(Subject).order_by(Subject.id))
    return list(result.scalars().all())


def get_by_id(db: Session, subject_id: int) -> Subject:
    subject = db.execute(select(Subject).where(Subject.id == subject_id)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return subject


def _get_majors_or_404(db: Session, major_ids: list[int]) -> list[Major]:
    majors = db.execute(
        select(Major).where(Major.id.in_(major_ids)).order_by(Major.id)
    ).scalars().all()
    found_ids = {major.id for major in majors}
    missing_ids = sorted(set(major_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Major not found: {missing_ids}",
        )
    return list(majors)


def _get_department_or_404(db: Session, department_id: int) -> Department:
    department = db.execute(
        select(Department).where(Department.id == department_id)
    ).scalar_one_or_none()
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


def create(db: Session, data: SubjectCreate) -> Subject:
    existing = db.execute(
        select(Subject).where((Subject.code == data.code) | (Subject.name == data.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exists")

    _get_department_or_404(db, data.department_id)
    majors = _get_majors_or_404(db, data.major_ids)

    subject = Subject(code=data.code, name=data.name, department_id=data.department_id)
    subject.majors = majors
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def update(db: Session, subject_id: int, data: SubjectUpdate) -> Subject:
    subject = get_by_id(db, subject_id)

    if data.code is not None and data.code != subject.code:
        existing = db.execute(
            select(Subject).where(Subject.code == data.code, Subject.id != subject_id)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exists")
        subject.code = data.code

    if data.name is not None and data.name != subject.name:
        existing = db.execute(
            select(Subject).where(Subject.name == data.name, Subject.id != subject_id)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exists")
        subject.name = data.name

    _get_department_or_404(db, data.department_id)
    subject.department_id = data.department_id

    majors = _get_majors_or_404(db, data.major_ids)
    subject.majors = majors

    db.commit()
    db.refresh(subject)
    return subject


def delete(db: Session, subject_id: int) -> None:
    subject = get_by_id(db, subject_id)
    db.delete(subject)
    db.commit()