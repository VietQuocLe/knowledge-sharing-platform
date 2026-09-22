from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Ensure project root is in sys.path when running worker standalone
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from arq import run_worker
from app.core.config import settings
from app.core.database import SessionLocal
from app.rag.ingestion.pipeline import ingest_asset
from app.services.conversion_service import convert_docx_to_pdf_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (Worker) %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
logging.getLogger("arq").setLevel(logging.INFO)
logger = logging.getLogger("arq_worker")
logger.setLevel(logging.INFO)


async def ingest_asset_task(ctx: dict, asset_id: int) -> bool:
    """
    ARQ Background Task: Extracts text, chunks, computes embeddings, and stores vectors.
    Runs inside a dedicated thread with an isolated database session.
    """
    logger.info("Starting ingest_asset_task for asset %s...", asset_id)

    def _sync_ingest() -> bool:
        with SessionLocal() as db:
            return ingest_asset(asset_id, db)

    try:
        success = await asyncio.to_thread(_sync_ingest)
        logger.info("Finished ingest_asset_task for asset %s (success=%s).", asset_id, success)
        return success
    except Exception as exc:
        logger.exception("Error during ingest_asset_task for asset %s: %s", asset_id, exc)
        return False


async def convert_docx_task(ctx: dict, asset_id: int) -> None:
    """
    ARQ Background Task: Converts DOCX asset to PDF (via Cloudmersive or LibreOffice)
    and then immediately triggers ingestion.
    Runs inside a dedicated thread with an isolated database session.
    """
    logger.info("Starting convert_docx_task for asset %s...", asset_id)

    def _sync_convert() -> None:
        convert_docx_to_pdf_task(asset_id)

    try:
        await asyncio.to_thread(_sync_convert)
        logger.info("Finished convert_docx_task for asset %s.", asset_id)
    except Exception as exc:
        logger.exception("Error during convert_docx_task for asset %s: %s", asset_id, exc)


async def startup(ctx: dict) -> None:
    """
    Worker startup hook: initializes resources and logs readiness.
    """
    logger.info("ARQ Worker initializing...")
    ctx["session_factory"] = SessionLocal
    logger.info("ARQ Worker ready. Listening for background jobs on Redis.")


async def shutdown(ctx: dict) -> None:
    """
    Worker shutdown hook: cleans up resources.
    """
    logger.info("ARQ Worker shutting down gracefully.")


class WorkerSettings:
    """
    ARQ Worker configuration.
    Consumed by `arq app.workers.worker.WorkerSettings` or `run_worker`.
    """
    functions = [ingest_asset_task, convert_docx_task]
    redis_settings = settings.get_redis_settings()
    max_jobs = settings.ARQ_MAX_JOBS
    job_timeout = settings.ARQ_JOB_TIMEOUT_SECONDS
    on_startup = startup
    on_shutdown = shutdown


def main() -> None:
    """
    CLI entry point to execute worker directly via Python:
    python -m app.workers.worker
    """
    print("\n" + "=" * 65, flush=True)
    print("   ARQ BACKGROUND WORKER ĐÃ KHỞI ĐỘNG THÀNH CÔNG!", flush=True)
    print(f"   Kết nối Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT} (db={settings.REDIS_DATABASE})", flush=True)
    print(f"   Các tasks đã đăng ký: {[f.__name__ for f in WorkerSettings.functions]}", flush=True)
    print("   Đang lắng nghe tác vụ từ Redis... (Nhấn Ctrl + C để dừng)", flush=True)
    print("=" * 65 + "\n", flush=True)

    try:
        run_worker(WorkerSettings)
    except KeyboardInterrupt:
        print("\n ARQ Worker đã dừng an toàn theo yêu cầu người dùng.", flush=True)


if __name__ == "__main__":
    main()

