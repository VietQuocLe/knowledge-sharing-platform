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

    # Ensure database schema exists
    Base.metadata.create_all(bind=engine)

    # Initialize system defaults
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

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router)