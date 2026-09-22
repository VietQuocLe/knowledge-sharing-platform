from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from arq import create_pool
from arq.connections import ArqRedis

from app.core.config import settings

logger = logging.getLogger(__name__)

_arq_pool: ArqRedis | None = None


async def get_arq_redis_pool() -> ArqRedis | None:
    """
    Retrieves or creates the global ARQ Redis connection pool.
    Returns None if Redis is unreachable, logging a warning rather than crashing.
    """
    global _arq_pool

    if _arq_pool is not None:
        return _arq_pool

    try:
        redis_settings = settings.get_redis_settings()
        logger.info(
            "Connecting to Redis for ARQ at %s:%s (db=%s)...",
            redis_settings.host,
            redis_settings.port,
            redis_settings.database,
        )
        _arq_pool = await create_pool(redis_settings)
        logger.info("Successfully established ARQ Redis connection pool.")
        return _arq_pool
    except Exception as exc:
        logger.warning(
            "Could not connect to Redis for ARQ (%s). Background jobs will fallback to in-process execution.",
            exc,
        )
        _arq_pool = None
        return None


async def close_arq_redis_pool() -> None:
    """
    Gracefully closes the global ARQ Redis pool connection.
    """
    global _arq_pool
    if _arq_pool is not None:
        try:
            logger.info("Closing ARQ Redis connection pool...")
            await _arq_pool.close()
        except Exception as exc:
            logger.warning("Error closing ARQ Redis pool: %s", exc)
        finally:
            _arq_pool = None

