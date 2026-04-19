"""Structured logging module."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.types import Processor


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None,
) -> None:
    """Setup structured logging configuration."""
    # Convert level string to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Set logging level for standard logging
    logging.basicConfig(level=log_level)

    # Common processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Add format-specific processors
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup file logging if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        file_handler.setLevel(log_level)

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding logging context."""

    def __init__(self, **kwargs: Any) -> None:
        self.context = kwargs

    def __enter__(self) -> "LogContext":
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        structlog.contextvars.unbind_contextvars(*self.context.keys())


def log_agent_event(
    logger: structlog.stdlib.BoundLogger,
    event: str,
    user_id: str,
    session_id: str,
    model: Optional[str] = None,
    skill: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log an agent event with standard fields."""
    with LogContext(
        user_id=user_id,
        session_id=session_id,
        model=model or "",
        skill=skill or "",
    ):
        logger.info(event, **kwargs)


def log_model_call(
    logger: structlog.stdlib.BoundLogger,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    success: bool,
    error: Optional[str] = None,
) -> None:
    """Log a model API call."""
    logger.info(
        "model_call",
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        latency_ms=latency_ms,
        success=success,
        error=error or "",
    )


def log_tool_execution(
    logger: structlog.stdlib.BoundLogger,
    tool_name: str,
    call_id: str,
    status: str,
    execution_time_ms: int,
    error: Optional[str] = None,
) -> None:
    """Log a tool execution."""
    logger.info(
        "tool_execution",
        tool=tool_name,
        call_id=call_id,
        status=status,
        execution_time_ms=execution_time_ms,
        error=error or "",
    )


def log_skill_usage(
    logger: structlog.stdlib.BoundLogger,
    skill_name: str,
    user_id: str,
    action: str,
    success: bool,
) -> None:
    """Log skill usage."""
    logger.info(
        "skill_usage",
        skill=skill_name,
        user_id=user_id,
        action=action,
        success=success,
    )