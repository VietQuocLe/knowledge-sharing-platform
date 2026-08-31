import functools
import inspect
import logging
import os
from typing import Any, Callable

from app.core.config import settings

logger = logging.getLogger(__name__)

# Check if Langfuse credentials are configured
_IS_LANGFUSE_ENABLED = bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)

if _IS_LANGFUSE_ENABLED:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

try:
    if _IS_LANGFUSE_ENABLED:
        from langfuse.decorators import langfuse_context, observe
    else:
        observe = None
        langfuse_context = None
except ImportError:
    observe = None
    langfuse_context = None
    _IS_LANGFUSE_ENABLED = False


def observe_llm(*decorator_args: Any, **decorator_kwargs: Any) -> Callable:
    """
    Decorator for tracing LLM functions with Langfuse.
    Acts as a transparent pass-through (no-op) if Langfuse is not enabled or keys are missing.
    Supports sync functions, async functions, and async generators.
    """
    def decorator(fn: Callable) -> Callable:
        if _IS_LANGFUSE_ENABLED and observe is not None:
            try:
                return observe(*decorator_args, **decorator_kwargs)(fn)
            except Exception as e:
                logger.warning(f"Failed to apply Langfuse observe decorator to {fn.__name__}: {e}")
                return fn
        
        # Transparent fallback (no-op)
        if inspect.isasyncgenfunction(fn):
            @functools.wraps(fn)
            async def async_gen_wrapper(*args: Any, **kwargs: Any):
                async for item in fn(*args, **kwargs):
                    yield item
            return async_gen_wrapper
        elif inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any):
                return await fn(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any):
                return fn(*args, **kwargs)
            return sync_wrapper

    # Handle being called as @observe_llm or @observe_llm(...)
    if len(decorator_args) == 1 and callable(decorator_args[0]) and not decorator_kwargs:
        actual_fn = decorator_args[0]
        decorator_args = ()
        return decorator(actual_fn)

    return decorator


def update_trace_context(**kwargs: Any) -> None:
    """
    Safe helper to update Langfuse trace metadata/tags.
    No-ops gracefully if Langfuse is disabled or not available.
    """
    if _IS_LANGFUSE_ENABLED and langfuse_context is not None:
        try:
            if "tags" in kwargs:
                langfuse_context.update_current_trace(tags=kwargs.pop("tags"))
            if kwargs:
                langfuse_context.update_current_trace(metadata=kwargs)
        except Exception as e:
            logger.debug(f"Langfuse context update skipped: {e}")

