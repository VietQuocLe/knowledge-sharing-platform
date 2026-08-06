from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models import Base
from app.services.startup_service import initialize_system


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app

    Base.metadata.create_all(bind=engine)

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

app.include_router(api_router)