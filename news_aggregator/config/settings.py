"""Application settings (environment-driven).

This module centralizes configuration to avoid hardcoding values across the codebase.
All settings can be overridden using environment variables.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Mapping, Sequence
from dotenv import load_dotenv
load_dotenv()

def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _get_env_int(name: str, default: int) -> int:
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _get_env_float(name: str, default: float) -> float:
    raw = _get_env(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    raw = _get_env(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _get_env_csv(name: str, default: Sequence[str]) -> list[str]:
    raw = _get_env(name)
    if raw is None:
        return list(default)
    items = [p.strip() for p in raw.split(",")]
    return [p for p in items if p]


def _get_env_json(name: str, default: Mapping[str, Any]) -> dict[str, Any]:
    raw = _get_env(name)
    if raw is None:
        return dict(default)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return dict(default)


def _require_env(name: str) -> str:
    value = _get_env(name)
    if value is None:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in your environment (or an .env file for local dev)."
        )
    return value


def _redact_db_url(url: str) -> str:
    # Best-effort redaction (keep scheme/host/db; drop password if present).
    try:
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(url)
        netloc = parts.netloc
        if "@" in netloc and ":" in netloc.split("@", 1)[0]:
            userinfo, hostinfo = netloc.split("@", 1)
            user = userinfo.split(":", 1)[0]
            netloc = f"{user}:***@{hostinfo}"
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    except Exception:
        return "<redacted>"


@dataclass(frozen=True, slots=True)
class Settings:
    """Strongly-typed application settings loaded from env."""

    # Core
    app_env: str
    log_level: str

    # Database
    database_url: str

    # RSS
    rss_urls: list[str]

    # Recommender weights
    weight_similarity: float
    weight_recency: float
    weight_source: float

    # Email (SMTP)
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_use_tls: bool
    email_from: str | None
    email_reply_to: str | None

    # Optional OpenAI summarization
    openai_api_key: str | None
    openai_model: str
    openai_base_url: str | None

    # Behavior toggles
    dry_run_email: bool

    @classmethod
    def load(cls) -> "Settings":
        rss_default = [
            # Top stories (US) - stable and broadly relevant
            "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        ]

        return cls(
            app_env=_get_env("APP_ENV", "local") or "local",
            log_level=_get_env("LOG_LEVEL", "INFO") or "INFO",
            # No silent fallbacks: explicit DATABASE_URL is required everywhere.
            database_url=_require_env("DATABASE_URL"),
            rss_urls=_get_env_csv("RSS_URLS", rss_default),
            weight_similarity=_get_env_float("REC_WEIGHT_SIMILARITY", 0.6),
            weight_recency=_get_env_float("REC_WEIGHT_RECENCY", 0.3),
            weight_source=_get_env_float("REC_WEIGHT_SOURCE", 0.1),
            smtp_host=_get_env("SMTP_HOST"),
            smtp_port=_get_env_int("SMTP_PORT", 587),
            smtp_user=_get_env("SMTP_USER"),
            smtp_password=_get_env("SMTP_PASSWORD"),
            smtp_use_tls=_get_env_bool("SMTP_USE_TLS", True),
            email_from=_get_env("EMAIL_FROM"),
            email_reply_to=_get_env("EMAIL_REPLY_TO"),
            openai_api_key=_get_env("OPENAI_API_KEY"),
            openai_model=_get_env("OPENAI_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
            openai_base_url=_get_env("OPENAI_BASE_URL"),
            dry_run_email=_get_env_bool("DRY_RUN_EMAIL", False),
        )

    def safe_summary(self) -> dict[str, Any]:
        """Return a JSON-serializable summary with secrets removed."""
        return {
            "app_env": self.app_env,
            "log_level": self.log_level,
            "database_url": _redact_db_url(self.database_url),
            "rss_urls": list(self.rss_urls),
            "weights": {
                "similarity": self.weight_similarity,
                "recency": self.weight_recency,
                "source": self.weight_source,
            },
            "smtp": {
                "host": self.smtp_host,
                "port": self.smtp_port,
                "user": self.smtp_user,
                "use_tls": self.smtp_use_tls,
                "email_from": self.email_from,
                "email_reply_to": self.email_reply_to,
                "configured": bool(self.smtp_host and self.smtp_user and self.smtp_password and self.email_from),
            },
            "openai": {
                "enabled": bool(self.openai_api_key),
                "model": self.openai_model,
                "base_url": self.openai_base_url,
            },
            "dry_run_email": self.dry_run_email,
        }


