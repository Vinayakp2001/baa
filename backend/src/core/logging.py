"""Structured JSON logging setup using structlog.

Provides:
- configure_logging(): call once at app startup
- get_logger(): returns a bound logger for use in any module
- bind_request_context(): middleware helper to bind per-request context
- Bound context keys: request_id, source_key, run_id
"""

import logging
import sys
import uuid
from contextvars import ContextVar

import structlog
from structlog.types import EventDict, WrappedLogger

from .config import settings

# ── Per-request context vars ─────────────────────────────────────────────────
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_source_key_var: ContextVar[str] = ContextVar("source_key", default="")
_run_id_var: ContextVar[str] = ContextVar("run_id", default="")
_entity_id_var: ContextVar[str] = ContextVar("entity_id", default="")


def _inject_context_vars(
    logger: WrappedLogger, method: str, event_dict: EventDict
) -> EventDict:
    """Structlog processor: inject request_id, source_key, run_id from context vars."""
    request_id = _request_id_var.get()
    source_key = _source_key_var.get()
    run_id = _run_id_var.get()
    entity_id = _entity_id_var.get()

    if request_id:
        event_dict["request_id"] = request_id
    if source_key:
        event_dict["source_key"] = source_key
    if run_id:
        event_dict["run_id"] = run_id
    if entity_id:
        event_dict["entity_id"] = entity_id

    return event_dict


def configure_logging() -> None:
    """Configure structlog for JSON output. Call once at application startup."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure stdlib logging to emit to stdout
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _inject_context_vars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Return a structlog bound logger for the given module name."""
    return structlog.get_logger(name)


def bind_pipeline_context(
    *,
    request_id: str | None = None,
    source_key: str | None = None,
    run_id: str | None = None,
    entity_id: str | None = None,
) -> None:
    """Bind pipeline context values to the current async context.

    These are propagated automatically into every log call in the same
    async task via structlog's contextvars support.
    """
    ctx: dict[str, str] = {}
    if request_id is not None:
        ctx["request_id"] = request_id
        _request_id_var.set(request_id)
    if source_key is not None:
        ctx["source_key"] = source_key
        _source_key_var.set(source_key)
    if run_id is not None:
        ctx["run_id"] = run_id
        _run_id_var.set(run_id)
    if entity_id is not None:
        ctx["entity_id"] = entity_id
        _entity_id_var.set(entity_id)
    if ctx:
        structlog.contextvars.bind_contextvars(**ctx)


def clear_pipeline_context() -> None:
    """Clear all bound pipeline context vars (call at end of request/task)."""
    structlog.contextvars.clear_contextvars()
    _request_id_var.set("")
    _source_key_var.set("")
    _run_id_var.set("")
    _entity_id_var.set("")
