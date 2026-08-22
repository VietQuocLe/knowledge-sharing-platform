from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.departments import router as departments_router
from app.api.health import router as health_router
from app.api.majors import router as majors_router
from app.api.subjects import router as subjects_router
from app.api.documents import router as documents_router
from app.api.config import router as config_router
from app.api.notebooks import router as notebooks_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(departments_router)
api_router.include_router(majors_router)
api_router.include_router(subjects_router)
api_router.include_router(documents_router)
api_router.include_router(config_router)
api_router.include_router(notebooks_router)