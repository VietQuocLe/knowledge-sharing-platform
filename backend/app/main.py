from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.include_router(api_router)