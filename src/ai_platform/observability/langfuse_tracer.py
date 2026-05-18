from __future__ import annotations

import functools
import logging
import time
import uuid
from typing import Any, Callable

logger = logging.getLogger(__name__)


def trace_node(node_id: str, workflow_name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        if __import__('asyncio').iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.monotonic()
                logger.info("[TRACE] node=%s workflow=%s status=start", node_id, workflow_name)
                result = await func(*args, **kwargs)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "[TRACE] node=%s workflow=%s status=end elapsed_ms=%.1f",
                    node_id, workflow_name, elapsed_ms,
                )
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.monotonic()
                logger.info("[TRACE] node=%s workflow=%s status=start", node_id, workflow_name)
                result = func(*args, **kwargs)
                elapsed_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "[TRACE] node=%s workflow=%s status=end elapsed_ms=%.1f",
                    node_id, workflow_name, elapsed_ms,
                )
                return result
            return sync_wrapper
    return decorator


def trace_llm_call(
    model: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> None:
    logger.info(
        "[LANGFUSE] LLM call model=%s prompt_tokens=%s completion_tokens=%s",
        model, prompt_tokens, completion_tokens,
    )


class LangfuseTracer:
    def start_trace(self, session_id: str) -> str:
        trace_id = uuid.uuid4().hex
        logger.debug("[LANGFUSE] trace_start session_id=%s trace_id=%s", session_id, trace_id)
        return trace_id

    def end_trace(self, trace_id: str) -> None:
        logger.debug("[LANGFUSE] trace_end trace_id=%s", trace_id)

    def log_span(self, trace_id: str, name: str, input: dict, output: dict) -> None:
        logger.debug(
            "[LANGFUSE] span trace_id=%s name=%s input_keys=%s output_keys=%s",
            trace_id, name, list(input.keys()), list(output.keys()),
        )
