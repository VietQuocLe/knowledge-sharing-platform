from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.database import get_db
from app.schemas.major import MajorCreate, MajorResponse, MajorUpdate
from app.services.major_service import create, delete, get_all, get_by_id, update

router = APIRouter(prefix="/majors", tags=["Majors"])


@router.get("/", response_model=list[MajorResponse])
def list_majors(
    department_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return get_all(db, department_id=department_id)


@router.get("/{major_id}", response_model=MajorResponse)
def read_major(major_id: int, db: Session = Depends(get_db)):
    return get_by_id(db, major_id)


@router.post("/", response_model=MajorResponse, dependencies=[Depends(require_admin)], status_code=201)
def create_major(data: MajorCreate, db: Session = Depends(get_db)):
    return create(db, data)


@router.put("/{major_id}", response_model=MajorResponse, dependencies=[Depends(require_admin)])
def update_major(major_id: int, data: MajorUpdate, db: Session = Depends(get_db)):
    return update(db, major_id, data)


@router.delete("/{major_id}", dependencies=[Depends(require_admin)], status_code=204)
def delete_major(major_id: int, db: Session = Depends(get_db)):
    delete(db, major_id)