from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.major import Major, major_subject
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


def _get_major_or_404(db: Session, major_id: int) -> Major:
    major = db.execute(select(Major).where(Major.id == major_id)).scalar_one_or_none()
    if major is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Major not found")
    return major


def get_all(
    db: Session,
    *,
    major_id: int | None = None,
    q: str | None = None,
    limit: int = 8,
) -> list[Subject]:
    if major_id is not None:
        _get_major_or_404(db, major_id)
        # Query both Subject and category from major_subject Table
        query = (
            select(Subject, major_subject.c.category)
            .options(selectinload(Subject.majors))
            .join(major_subject, Subject.id == major_subject.c.subject_id)
            .where(major_subject.c.major_id == major_id)
        )
        if q is not None:
            query = query.where(
                (Subject.name.ilike(f"%{q}%")) | (Subject.code.ilike(f"%{q}%"))
            )
        
        query = query.order_by(Subject.id)
        if q is not None:
            query = query.limit(limit)

        result = db.execute(query).all()
        subjects = []
        for subject, category in result:
            subject.category = category
            subjects.append(subject)
        return subjects
    else:
        query = select(Subject).options(selectinload(Subject.majors))
        if q is not None:
            query = query.where(
                (Subject.name.ilike(f"%{q}%")) | (Subject.code.ilike(f"%{q}%"))
            )
        
        query = query.order_by(Subject.id)
        if q is not None:
            query = query.limit(limit)

        subjects = list(db.execute(query).scalars().all())
        for subject in subjects:
            subject.category = None
        return subjects


def get_by_id(db: Session, subject_id: int) -> Subject:
    subject = db.execute(select(Subject).where(Subject.id == subject_id)).scalar_one_or_none()
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    subject.category = None
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



def create(db: Session, data: SubjectCreate) -> Subject:
    existing = db.execute(
        select(Subject).where((Subject.code == data.code) | (Subject.name == data.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject already exists")

    majors = _get_majors_or_404(db, data.major_ids)

    subject = Subject(code=data.code, name=data.name)
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

    if data.major_ids is not None:
        majors = _get_majors_or_404(db, data.major_ids)
        subject.majors = majors

    db.commit()
    db.refresh(subject)
    return subject


def delete(db: Session, subject_id: int) -> None:
    subject = get_by_id(db, subject_id)
    db.delete(subject)
    db.commit()