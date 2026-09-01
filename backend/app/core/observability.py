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

observe = None
langfuse_context = None
_langfuse_client = None

if _IS_LANGFUSE_ENABLED:
    try:
        # 1. Try Langfuse v4+ root export
        try:
            from langfuse import observe, get_client
            try:
                _langfuse_client = get_client()
            except Exception as e:
                logger.debug(f"Langfuse get_client skipped: {e}")
        except ImportError:
            # 2. Fallback to Langfuse v2/v3 decorators module
            from langfuse.decorators import observe, langfuse_context

        # 3. Check for langfuse_context if not yet loaded
        if langfuse_context is None:
            try:
                from langfuse.decorators import langfuse_context
            except ImportError:
                try:
                    from langfuse import langfuse_context
                except ImportError:
                    langfuse_context = None

    except Exception as e:
        logger.warning(f"Failed to initialize Langfuse SDK: {e}")
        observe = None
        langfuse_context = None
        _langfuse_client = None
        _IS_LANGFUSE_ENABLED = False


def flush_langfuse() -> None:
    """
    Safe helper to flush Langfuse events (useful for CLI scripts/processes before exit).
    No-ops gracefully if Langfuse is disabled or not available.
    """
    if _IS_LANGFUSE_ENABLED:
        try:
            if _langfuse_client is not None and hasattr(_langfuse_client, "flush"):
                _langfuse_client.flush()
            elif langfuse_context is not None and hasattr(langfuse_context, "flush"):
                langfuse_context.flush()
        except Exception as e:
            logger.debug(f"Langfuse flush failed: {e}")


def get_default_trace_metadata() -> dict[str, Any]:
    """
    Returns standard system-wide metadata identifying model versions and environment.
    """
    return {
        "environment": "development" if settings.DEBUG else "production",
        "chat_model": settings.GEMINI_CHAT_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
    }


def observe_llm(*decorator_args: Any, **decorator_kwargs: Any) -> Callable:
    """
    Decorator for tracing LLM functions with Langfuse.
    Acts as a transparent pass-through (no-op) if Langfuse is not enabled or keys are missing.
    Supports sync functions, async functions, and async generators.
    Automatically injects default trace metadata.
    """
    def decorator(fn: Callable) -> Callable:
        if _IS_LANGFUSE_ENABLED and observe is not None:
            try:
                observed_fn = observe(*decorator_args, **decorator_kwargs)(fn)

                if inspect.isasyncgenfunction(fn):
                    @functools.wraps(fn)
                    async def async_gen_wrapper(*args: Any, **kwargs: Any):
                        update_trace_context()
                        async for item in observed_fn(*args, **kwargs):
                            yield item
                    return async_gen_wrapper
                elif inspect.iscoroutinefunction(fn):
                    @functools.wraps(fn)
                    async def async_wrapper(*args: Any, **kwargs: Any):
                        update_trace_context()
                        return await observed_fn(*args, **kwargs)
                    return async_wrapper
                else:
                    @functools.wraps(fn)
                    def sync_wrapper(*args: Any, **kwargs: Any):
                        update_trace_context()
                        return observed_fn(*args, **kwargs)
                    return sync_wrapper
            except Exception as e:
                logger.warning(f"Failed to apply Langfuse observe decorator to {fn.__name__}: {e}")
                return fn
        
        # Transparent fallback (no-op)
        if inspect.isasyncgenfunction(fn):
            @functools.wraps(fn)
            async def async_gen_fallback(*args: Any, **kwargs: Any):
                async for item in fn(*args, **kwargs):
                    yield item
            return async_gen_fallback
        elif inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_fallback(*args: Any, **kwargs: Any):
                return await fn(*args, **kwargs)
            return async_fallback
        else:
            @functools.wraps(fn)
            def sync_fallback(*args: Any, **kwargs: Any):
                return fn(*args, **kwargs)
            return sync_fallback

    # Handle being called as @observe_llm or @observe_llm(...)
    if len(decorator_args) == 1 and callable(decorator_args[0]) and not decorator_kwargs:
        actual_fn = decorator_args[0]
        decorator_args = ()
        return decorator(actual_fn)

    return decorator


def update_trace_context(**kwargs: Any) -> None:
    """
    Safe helper to update Langfuse trace metadata/tags.
    Automatically merges default metadata (environment, chat_model, embedding_model).
    Supports both Langfuse v4 client and legacy langfuse_context.
    No-ops gracefully if Langfuse is disabled or not available.
    """
    if not _IS_LANGFUSE_ENABLED:
        return

    try:
        tags = kwargs.pop("tags", None)
        user_id = kwargs.pop("user_id", None)
        session_id = kwargs.pop("session_id", None)

        combined_metadata = {**get_default_trace_metadata(), **kwargs}

        if langfuse_context is not None and hasattr(langfuse_context, "update_current_trace"):
            trace_update: dict[str, Any] = {"metadata": combined_metadata}
            if tags is not None:
                trace_update["tags"] = tags
            if user_id is not None:
                trace_update["user_id"] = user_id
            if session_id is not None:
                trace_update["session_id"] = session_id
            langfuse_context.update_current_trace(**trace_update)
        elif _langfuse_client is not None and hasattr(_langfuse_client, "update_current_span"):
            try:
                _langfuse_client.update_current_span(metadata=combined_metadata)
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Langfuse context update skipped: {e}")


def update_current_observation(**kwargs: Any) -> None:
    """
    Safe helper to update Langfuse current observation (generation/span details: model, input, output, usage, metadata).
    Supports both Langfuse v4 client and legacy langfuse_context.
    No-ops gracefully if Langfuse is disabled or not available.
    """
    if not _IS_LANGFUSE_ENABLED:
        return

    try:
        # Standardize usage vs usage_details for v4 compatibility
        if "usage" in kwargs and "usage_details" not in kwargs:
            kwargs["usage_details"] = kwargs.pop("usage")

        if _langfuse_client is not None and hasattr(_langfuse_client, "update_current_generation"):
            try:
                _langfuse_client.update_current_generation(**kwargs)
                return
            except Exception:
                # If current observation is a span rather than generation, fallback to update_current_span
                span_kwargs = {k: v for k, v in kwargs.items() if k in ["name", "input", "output", "metadata", "level", "status_message"]}
                if span_kwargs:
                    _langfuse_client.update_current_span(**span_kwargs)
                return

        if langfuse_context is not None and hasattr(langfuse_context, "update_current_observation"):
            langfuse_context.update_current_observation(**kwargs)
    except Exception as e:
        logger.debug(f"Langfuse observation update skipped: {e}")

