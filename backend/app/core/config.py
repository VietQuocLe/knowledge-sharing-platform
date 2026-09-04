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
    MINIO_API_PORT: int = 9000
    MINIO_CONSOLE_PORT: int = 9001
    MINIO_BUCKET_NAME: str = "resources"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_ENDPOINT: str | None = None

    # Upload System & Notebooks Quotas
    MAX_FILE_SIZE_MB: int = 30
    ALLOWED_UPLOAD_FILE_TYPES: list[str] = ["PDF", "DOCX"]
    MAX_SOURCES_PER_NOTEBOOK: int = 10
    MAX_ARTIFACTS_PER_NOTEBOOK: int = 20
    ARTIFACT_GENERATION_COOLDOWN_SECONDS: int = 15

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Default Admin
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_FULL_NAME: str = "Quản trị viên Hệ thống"

    # Gemini / Embedding
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    # General AI Settings
    EMBEDDING_DIMENSION: int = 768
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite"
    EMBEDDING_PROVIDER: str = "gemini"  # "gemini" | "jina"

    # ─── Embedding: Gemini Settings ───
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    GEMINI_EMBEDDING_RPM_LIMIT: int = 80
    GEMINI_EMBEDDING_TPM_LIMIT: int = 26000
    GEMINI_EMBEDDING_TPM_BUDGET_PER_BATCH: int = 24000
    GEMINI_EMBEDDING_MAX_CHUNKS_PER_BATCH: int = 80
    GEMINI_EMBEDDING_WINDOW_SECONDS: float = 60.0
    GEMINI_EMBEDDING_RETRY_ATTEMPTS: int = 6
    GEMINI_EMBEDDING_RETRY_MULTIPLIER: float = 2.0
    GEMINI_EMBEDDING_RETRY_MIN_WAIT: float = 5.0
    GEMINI_EMBEDDING_RETRY_MAX_WAIT: float = 60.0

    # ─── Embedding: Jina Settings (Tối ưu cho Jina v3 Free Tier: 500 RPM, 50 chunks/batch) ───
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v3"
    JINA_EMBEDDING_TIMEOUT_SECONDS: float = 15.0
    JINA_EMBEDDING_RPM_LIMIT: int = 120                 # Jina free tier hỗ trợ tới 500 RPM, 120 RPM giúp ingest nhanh
    JINA_EMBEDDING_TPM_LIMIT: int = 100000              # Jina không bị bóp 30k TPM như Gemini, đặt 100k TPM
    JINA_EMBEDDING_TPM_BUDGET_PER_BATCH: int = 25000    # ~25.000 tokens mỗi batch gửi sang Jina
    JINA_EMBEDDING_MAX_CHUNKS_PER_BATCH: int = 50       # 50 chunks/batch gửi HTTP payload nhỏ gọn, tránh timeout
    JINA_EMBEDDING_WINDOW_SECONDS: float = 60.0
    JINA_EMBEDDING_RETRY_ATTEMPTS: int = 5              # Tự động thử lại 5 lần khi gặp 429 hoặc timeout
    JINA_EMBEDDING_RETRY_MULTIPLIER: float = 2.0
    JINA_EMBEDDING_RETRY_MIN_WAIT: float = 2.0
    JINA_EMBEDDING_RETRY_MAX_WAIT: float = 30.0

    # Document Ingestion & Chunking (Dùng chung)
    INGESTION_CHUNK_SIZE_WORDS: int = 600
    INGESTION_CHUNK_OVERLAP_WORDS: int = 100
    INGESTION_MIN_PDF_CHAR_THRESHOLD: int = 100

    # RAG Retrieval & Hybrid Search
    GEMINI_RETRIEVAL_EMBED_RETRY_ATTEMPTS: int = 3
    GEMINI_RETRIEVAL_EMBED_RETRY_MULTIPLIER: float = 1.0
    GEMINI_RETRIEVAL_EMBED_RETRY_MIN_WAIT: float = 2.0
    GEMINI_RETRIEVAL_EMBED_RETRY_MAX_WAIT: float = 3.0
    RAG_DENSE_SEARCH_TOP_K: int = 20
    RAG_SPARSE_SEARCH_TOP_K: int = 20
    RAG_RRF_K: float = 60.0
    RAG_RRF_TOP_K: int = 5
    RAG_CONTEXT_MAX_TOKENS: int = 3000

    # Two-Stage Reranking (Jina AI)
    ENABLE_RERANKER: bool = True
    JINA_API_KEY: str | None = None
    JINA_RERANK_MODEL: str = "jina-reranker-v2-base-multilingual"
    JINA_RERANK_TIMEOUT_SECONDS: float = 5.0
    RAG_RRF_POOL_SIZE: int = 15
    RAG_RERANK_TOP_N: int = 5

    # Notebook Chat & Condensation
    CHAT_HISTORY_SLIDING_WINDOW_SIZE: int = 6
    GEMINI_CONDENSE_RETRY_ATTEMPTS: int = 3
    GEMINI_CONDENSE_RETRY_MULTIPLIER: float = 1.0
    GEMINI_CONDENSE_RETRY_MIN_WAIT: float = 2.0
    GEMINI_CONDENSE_RETRY_MAX_WAIT: float = 10.0

    # Artifacts & Quotas
    QUIZ_GENERATION_CHUNK_BUDGET: int = 30
    GEMINI_QUIZ_RETRY_ATTEMPTS: int = 3
    GEMINI_QUIZ_RETRY_MULTIPLIER: float = 1.0
    GEMINI_QUIZ_RETRY_MIN_WAIT: float = 2.0
    GEMINI_QUIZ_RETRY_MAX_WAIT: float = 10.0

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    # Document Conversion
    CLOUDMERSIVE_API_KEY: str | None = None
    CLOUDMERSIVE_TIMEOUT_SECONDS: float = 60.0
    LIBREOFFICE_TIMEOUT_SECONDS: int = 60

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

    @property
    def ACTIVE_EMBEDDING_RPM_LIMIT(self) -> int:
        return self.JINA_EMBEDDING_RPM_LIMIT if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_RPM_LIMIT

    @property
    def ACTIVE_EMBEDDING_TPM_LIMIT(self) -> int:
        return self.JINA_EMBEDDING_TPM_LIMIT if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_TPM_LIMIT

    @property
    def ACTIVE_EMBEDDING_TPM_BUDGET_PER_BATCH(self) -> int:
        return self.JINA_EMBEDDING_TPM_BUDGET_PER_BATCH if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_TPM_BUDGET_PER_BATCH

    @property
    def ACTIVE_EMBEDDING_MAX_CHUNKS_PER_BATCH(self) -> int:
        return self.JINA_EMBEDDING_MAX_CHUNKS_PER_BATCH if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_MAX_CHUNKS_PER_BATCH

    @property
    def ACTIVE_EMBEDDING_WINDOW_SECONDS(self) -> float:
        return self.JINA_EMBEDDING_WINDOW_SECONDS if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_WINDOW_SECONDS

    @property
    def ACTIVE_EMBEDDING_RETRY_ATTEMPTS(self) -> int:
        return self.JINA_EMBEDDING_RETRY_ATTEMPTS if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_RETRY_ATTEMPTS

    @property
    def ACTIVE_EMBEDDING_RETRY_MULTIPLIER(self) -> float:
        return self.JINA_EMBEDDING_RETRY_MULTIPLIER if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_RETRY_MULTIPLIER

    @property
    def ACTIVE_EMBEDDING_RETRY_MIN_WAIT(self) -> float:
        return self.JINA_EMBEDDING_RETRY_MIN_WAIT if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_RETRY_MIN_WAIT

    @property
    def ACTIVE_EMBEDDING_RETRY_MAX_WAIT(self) -> float:
        return self.JINA_EMBEDDING_RETRY_MAX_WAIT if self.EMBEDDING_PROVIDER.lower() == "jina" else self.GEMINI_EMBEDDING_RETRY_MAX_WAIT


settings = Settings()