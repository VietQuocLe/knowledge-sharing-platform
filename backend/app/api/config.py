from fastapi import APIRouter
from app.core.config import settings

# Trigger reload
router = APIRouter(prefix="/config", tags=["Config"])


@router.get("/upload")
def get_upload_config():
    return {
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "allowed_upload_file_types": settings.ALLOWED_UPLOAD_FILE_TYPES,
    }
