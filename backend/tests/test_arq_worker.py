import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from arq.connections import RedisSettings

from app.core.config import Settings
from app.workers.worker import (
    WorkerSettings,
    convert_docx_task,
    ingest_asset_task,
    shutdown,
    startup,
)


def test_redis_settings_default():
    """Verify default RedisSettings generation from individual parameters."""
    cfg = Settings(
        REDIS_HOST="127.0.0.1",
        REDIS_PORT=6380,
        REDIS_PASSWORD="mypassword",
        REDIS_DATABASE=3,
        REDIS_URL=None,
    )
    rs = cfg.get_redis_settings()
    assert isinstance(rs, RedisSettings)
    assert rs.host == "127.0.0.1"
    assert rs.port == 6380
    assert rs.password == "mypassword"
    assert rs.database == 3


def test_redis_settings_from_url():
    """Verify RedisSettings generation when REDIS_URL DSN is provided."""
    cfg = Settings(
        REDIS_URL="redis://:supersecret@myredishost:6389/5",
    )
    rs = cfg.get_redis_settings()
    assert isinstance(rs, RedisSettings)
    assert rs.host == "myredishost"
    assert rs.port == 6389
    assert rs.password == "supersecret"
    assert rs.database == 5


def test_worker_settings_attributes():
    """Verify WorkerSettings has registered all tasks and configurations."""
    assert ingest_asset_task in WorkerSettings.functions
    assert convert_docx_task in WorkerSettings.functions
    assert WorkerSettings.max_jobs > 0
    assert WorkerSettings.job_timeout >= 60


@pytest.mark.asyncio
async def test_worker_lifecycle_hooks():
    """Verify worker startup and shutdown hooks execute cleanly."""
    ctx = {}
    await startup(ctx)
    assert "session_factory" in ctx

    await shutdown(ctx)


@pytest.mark.asyncio
async def test_ingest_asset_task_execution():
    """Verify ingest_asset_task runs in a thread with isolated session."""
    with patch("app.workers.worker.ingest_asset", return_value=True) as mock_ingest:
        result = await ingest_asset_task({}, 101)
        assert result is True
        mock_ingest.assert_called_once()
        args, kwargs = mock_ingest.call_args
        assert args[0] == 101
        # Second argument must be a database session instance
        assert args[1] is not None


@pytest.mark.asyncio
async def test_convert_docx_task_execution():
    """Verify convert_docx_task runs in a thread calling conversion pipeline."""
    with patch("app.workers.worker.convert_docx_to_pdf_task") as mock_convert:
        await convert_docx_task({}, 202)
        mock_convert.assert_called_once_with(202)


@pytest.mark.asyncio
async def test_upload_notebook_asset_enqueues_to_arq():
    """Verify upload_notebook_asset enqueues to ARQ Redis pool when available."""
    from app.services import notebook_service
    from app.models.enums import UserRole, SubscriptionTier
    from app.models.user import User
    from app.models.notebook import Notebook

    db_mock = MagicMock()
    user = User(id=1, role=UserRole.USER, tier=SubscriptionTier.PRO)
    notebook = Notebook(id=5, owner_id=1)

    # Mock notebook query
    db_mock.execute.return_value.scalar_one_or_none.return_value = notebook

    mock_pool = AsyncMock()
    mock_job = MagicMock()
    mock_job.job_id = "job-12345"
    mock_pool.enqueue_job.return_value = mock_job

    bg_tasks_mock = MagicMock()

    # Provide minimal valid PDF header
    valid_pdf_bytes = b"%PDF-1.4 test content with minimum bytes"

    with patch("app.services.storage_service.upload_object"), \
         patch("app.services.quota_service.check_sources_quota"):
        asset = await notebook_service.upload_notebook_asset(
            db=db_mock,
            user=user,
            notebook_id=5,
            file_name="test.pdf",
            file_bytes=valid_pdf_bytes,
            background_tasks=bg_tasks_mock,
            arq_pool=mock_pool,
        )

        assert asset is not None
        mock_pool.enqueue_job.assert_called_once_with("ingest_asset_task", asset.id)
        # Since ARQ succeeded, background_tasks should NOT be used as fallback
        bg_tasks_mock.add_task.assert_not_called()


@pytest.mark.asyncio
async def test_upload_notebook_asset_falls_back_when_arq_fails():
    """Verify upload_notebook_asset falls back to BackgroundTasks if ARQ enqueue fails."""
    from app.services import notebook_service
    from app.models.enums import UserRole, SubscriptionTier
    from app.models.user import User
    from app.models.notebook import Notebook

    db_mock = MagicMock()
    user = User(id=1, role=UserRole.USER, tier=SubscriptionTier.PRO)
    notebook = Notebook(id=5, owner_id=1)

    db_mock.execute.return_value.scalar_one_or_none.return_value = notebook

    mock_pool = AsyncMock()
    mock_pool.enqueue_job.side_effect = ConnectionError("Redis connection lost")

    bg_tasks_mock = MagicMock()
    valid_pdf_bytes = b"%PDF-1.4 test content with minimum bytes"

    with patch("app.services.storage_service.upload_object"), \
         patch("app.services.quota_service.check_sources_quota"):
        asset = await notebook_service.upload_notebook_asset(
            db=db_mock,
            user=user,
            notebook_id=5,
            file_name="test.pdf",
            file_bytes=valid_pdf_bytes,
            background_tasks=bg_tasks_mock,
            arq_pool=mock_pool,
        )

        assert asset is not None
        # Must fall back to in-process background_tasks
        bg_tasks_mock.add_task.assert_called_once()

