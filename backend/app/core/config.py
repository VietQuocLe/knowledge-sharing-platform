from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Knowledge Sharing Platform"
    DEBUG: bool = False

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
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite"

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