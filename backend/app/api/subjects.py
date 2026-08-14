from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.database import get_db
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.subject_service import create, delete, get_all, get_by_id, update

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("/", response_model=list[SubjectResponse])
def list_subjects(
    major_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_all(db, major_id=major_id)


@router.get("/{subject_id}", response_model=SubjectResponse)
def read_subject(subject_id: int, db: Session = Depends(get_db)):
    return get_by_id(db, subject_id)


@router.post("/", response_model=SubjectResponse, dependencies=[Depends(require_admin)], status_code=201)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    return create(db, data)


@router.put("/{subject_id}", response_model=SubjectResponse, dependencies=[Depends(require_admin)])
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db)):
    return update(db, subject_id, data)


@router.delete("/{subject_id}", dependencies=[Depends(require_admin)], status_code=204)
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    delete(db, subject_id)