"""RSS fetching and normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import time
from typing import Iterable, Optional, Sequence

import feedparser
from dateutil import parser as date_parser
from sqlalchemy import select
import re
from news_aggregator.config.settings import Settings
from news_aggregator.models.database import Article, get_engine, get_session_factory, session_scope

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NormalizedArticle:
    title: str
    link: str
    published_at: datetime | None
    summary: str | None
    source: str | None


class RSSFetcher:
    """Fetch and normalize articles from RSS feeds."""

    def __init__(self, rss_urls: Sequence[str]) -> None:
        self._rss_urls = list(rss_urls)

    def fetch(self) -> list[NormalizedArticle]:
        articles: list[NormalizedArticle] = []
        for url in self._rss_urls:
            articles.extend(self._fetch_one_with_retries(url))
        return articles

    def _fetch_one_with_retries(self, url: str) -> list[NormalizedArticle]:
        # Lightweight fault tolerance for transient network/DNS issues.
        delays_s = (1.0, 2.0, 4.0)
        last_exc: Exception | None = None
        for i, delay in enumerate(delays_s, start=1):
            try:
                return self._fetch_one(url)
            except Exception as e:
                last_exc = e
                logger.warning("RSS fetch attempt %d/%d failed for url=%s err=%r", i, len(delays_s), url, e)
                time.sleep(delay)
        logger.error("RSS fetch failed after retries for url=%s err=%r", url, last_exc)
        return []

    def _fetch_one(self, url: str) -> list[NormalizedArticle]:
        parsed = feedparser.parse(url)
        if getattr(parsed, "bozo", 0):
            # feedparser uses bozo flag to indicate parsing issues; still may have entries.
            logger.warning("RSS parse bozo=1 for url=%s error=%r", url, getattr(parsed, "bozo_exception", None))

        feed_title = None
        try:
            feed_title = getattr(parsed.feed, "title", None)
        except Exception:
            feed_title = None

        out: list[NormalizedArticle] = []
        for entry in getattr(parsed, "entries", []) or []:
            title = (getattr(entry, "title", None) or "").strip()
            link = (getattr(entry, "link", None) or "").strip()
            if not title or not link:
                continue

            published_at = _parse_entry_datetime(entry)
            summary = _extract_summary(entry)
            source = _extract_source(entry) or feed_title

            out.append(
                NormalizedArticle(
                    title=title,
                    link=link,
                    published_at=published_at,
                    summary=summary,
                    source=source,
                )
            )
        logger.info("Fetched %d entries from %s", len(out), url)
        return out


class RSSIngestor:
    """Persist normalized RSS articles into the database (dedup by link)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = get_engine(settings.database_url, echo=False)
        self._session_factory = get_session_factory(self._engine)

    def ingest(self, articles: Iterable[NormalizedArticle]) -> int:
        inserted = 0
        with session_scope(self._session_factory) as session:
            for a in articles:
                if self._exists_by_link(session, a.link):
                    continue
                session.add(
                    Article(
                        title=a.title,
                        link=a.link,
                        published_at=a.published_at,
                        summary=a.summary,
                        source=a.source,
                        content=None,
                    )
                )
                inserted += 1
        logger.info("Ingested %d new articles", inserted)
        return inserted

    @staticmethod
    def _exists_by_link(session, link: str) -> bool:
        stmt = select(Article.id).where(Article.link == link).limit(1)
        return session.execute(stmt).first() is not None


def fetch_and_ingest(settings: Settings) -> int:
    """Convenience entrypoint for scheduler/CLI later."""
    fetcher = RSSFetcher(settings.rss_urls)
    articles = fetcher.fetch()
    ingestor = RSSIngestor(settings)
    return ingestor.ingest(articles)


def _parse_entry_datetime(entry) -> datetime | None:
    for key in ("published", "updated"):
        raw = getattr(entry, key, None)
        if raw:
            try:
                dt = date_parser.parse(str(raw))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                continue
    return None




def _extract_summary(entry) -> str | None:
    raw = getattr(entry, "summary", None) or getattr(entry, "description", None)
    if not raw:
        return None

    text = str(raw)

    # REMOVE HTML TAGS
    clean = re.sub(r"<.*?>", "", text)

    return clean.strip() if clean else None


def _extract_source(entry) -> str | None:
    # Try common places where source might appear.
    source = getattr(entry, "source", None)
    if isinstance(source, dict):
        name = source.get("title") or source.get("name")
        return str(name).strip() if name else None
    if source is not None:
        name = getattr(source, "title", None) or getattr(source, "name", None)
        return str(name).strip() if name else None
    return None

