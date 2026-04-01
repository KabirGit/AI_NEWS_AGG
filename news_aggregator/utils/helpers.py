"""Common helpers shared across modules."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from logging import Logger
from typing import Optional

from news_aggregator.config.settings import Settings


def utcnow() -> datetime:
    """Timezone-aware UTC now."""
    return datetime.now(tz=timezone.utc)


def setup_logging(settings: Settings, logger_name: str = "news_aggregator") -> Logger:
    """Configure stdlib logging and return an app logger.

    Keeps configuration simple and centralized; modules should call `logging.getLogger(__name__)`
    after this runs.
    """
    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers when re-running in Streamlit or REPL.
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)

    return logging.getLogger(logger_name)


def is_smtp_configured(settings: Settings) -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_user
        and settings.smtp_password
        and settings.email_from
        and settings.smtp_port > 0
    )


