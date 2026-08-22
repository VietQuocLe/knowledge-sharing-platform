from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notebook import NotebookCreate, NotebookRead
from app.services import notebook_service

router = APIRouter(prefix="/notebooks", tags=["Notebooks"])


@router.post("/", response_model=NotebookRead, status_code=status.HTTP_201_CREATED)
def create_notebook(
    data: NotebookCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.create_notebook(db, current_user, data)


@router.get("/me", response_model=list[NotebookRead])
def list_my_notebooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return notebook_service.get_notebooks_by_owner(db, current_user)
