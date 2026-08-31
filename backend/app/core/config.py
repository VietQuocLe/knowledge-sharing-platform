from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Knowledge Sharing Platform"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        return []

    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # MinIO
    MINIO_HOST: str = "localhost"
    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str
    MINIO_API_PORT: int
    MINIO_CONSOLE_PORT: int
    MINIO_BUCKET_NAME: str = "resources"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_ENDPOINT: str | None = None

    # Upload System
    MAX_FILE_SIZE_MB: int = 30
    ALLOWED_UPLOAD_FILE_TYPES: list[str] = ["PDF", "DOCX"]

    # Notebooks
    MAX_SOURCES_PER_NOTEBOOK: int = 10

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Default Admin
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_FULL_NAME: str

    # Gemini / Embedding
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_EMBEDDING_RPM_LIMIT: int = 80
    GEMINI_EMBEDDING_TPM_LIMIT: int = 26000
    GEMINI_EMBEDDING_TPM_BUDGET_PER_BATCH: int = 24000
    GEMINI_EMBEDDING_MAX_CHUNKS_PER_BATCH: int = 80

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Cloudmersive Document Conversion
    CLOUDMERSIVE_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def MAX_UPLOAD_FILE_SIZE_MB(self) -> int:
        return self.MAX_FILE_SIZE_MB


settings = Settings()