from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models import Base
from app.services.startup_service import initialize_system


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app

    # Khởi tạo schema database
    Base.metadata.create_all(bind=engine)

    # Seed dữ liệu mặc định hệ thống
    db = SessionLocal()
    try:
        initialize_system(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# Cấu hình CORS middleware theo Enterprise Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn routing toàn bộ hệ thống
app.include_router(api_router)