from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.core.database import get_db
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.services.department_service import create, delete, get_all, get_by_id, update

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("/", response_model=list[DepartmentResponse])
def list_departments(db: Session = Depends(get_db)):
    return get_all(db)


@router.get("/{department_id}", response_model=DepartmentResponse)
def read_department(department_id: int, db: Session = Depends(get_db)):
    return get_by_id(db, department_id)


@router.post("/", response_model=DepartmentResponse, dependencies=[Depends(require_admin)], status_code=201)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    return create(db, data)


@router.put("/{department_id}", response_model=DepartmentResponse, dependencies=[Depends(require_admin)])
def update_department(department_id: int, data: DepartmentUpdate, db: Session = Depends(get_db)):
    return update(db, department_id, data)


@router.delete("/{department_id}", dependencies=[Depends(require_admin)], status_code=204)
def delete_department(department_id: int, db: Session = Depends(get_db)):
    delete(db, department_id)