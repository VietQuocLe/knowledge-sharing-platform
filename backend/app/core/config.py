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
    FREE_MAX_SOURCES: int = 8
    PRO_MAX_SOURCES: int = 20
    FREE_MAX_ARTIFACTS: int = 10
    PRO_MAX_ARTIFACTS: int = 20
    PRO_PLAN_PRICE: int = 49000
    MAX_SOURCES_PER_NOTEBOOK: int = 8
    MAX_ARTIFACTS_PER_NOTEBOOK: int = 10
    ARTIFACT_GENERATION_COOLDOWN_SECONDS: int = 15

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Default Admin
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_FULL_NAME: str = "Quản trị viên Hệ thống"

    # AI & LLM Settings
    GOOGLE_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    EMBEDDING_DIMENSION: int = 768
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite"
    EMBEDDING_PROVIDER: str = "jina"

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

    # ─── Embedding: Jina Settings ───
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v3"
    JINA_EMBEDDING_TIMEOUT_SECONDS: float = 15.0
    JINA_EMBEDDING_RPM_LIMIT: int = 120
    JINA_EMBEDDING_TPM_LIMIT: int = 100000
    JINA_EMBEDDING_TPM_BUDGET_PER_BATCH: int = 25000
    JINA_EMBEDDING_MAX_CHUNKS_PER_BATCH: int = 50
    JINA_EMBEDDING_WINDOW_SECONDS: float = 60.0
    JINA_EMBEDDING_RETRY_ATTEMPTS: int = 5
    JINA_EMBEDDING_RETRY_MULTIPLIER: float = 2.0
    JINA_EMBEDDING_RETRY_MIN_WAIT: float = 2.0
    JINA_EMBEDDING_RETRY_MAX_WAIT: float = 30.0

    # Document Ingestion & Chunking
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

    # VNPay Configuration
    VNPAY_TMN_CODE: str = "2QX2851U"
    VNPAY_SECURE_SECRET: str = "A4O2PBLT0L7I2RLLNQLR8H7Z22W77J6A"
    VNPAY_PAYMENT_URL: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    VNPAY_RETURN_URL: str = "http://localhost:5173/payment/vnpay-return"
    VNPAY_IPN_URL: str = "http://localhost:8000/payments/vnpay-ipn"

    # Redis & ARQ Worker Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DATABASE: int = 0
    REDIS_URL: str | None = None
    ARQ_MAX_JOBS: int = 10
    ARQ_JOB_TIMEOUT_SECONDS: int = 300

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
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

    def get_redis_settings(self):
        """
        Builds and returns an arq RedisSettings instance.
        Supports both REDIS_URL (DSN) and individual host/port/password parameters.
        """
        from arq.connections import RedisSettings

        if self.REDIS_URL:
            return RedisSettings.from_dsn(self.REDIS_URL)
        return RedisSettings(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            password=self.REDIS_PASSWORD if self.REDIS_PASSWORD else None,
            database=self.REDIS_DATABASE,
        )


settings = Settings()