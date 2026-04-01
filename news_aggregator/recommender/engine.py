"""Recommendation engine (TF-IDF + cosine similarity).

Phase 0 skeleton: implementation will follow in Phase 5.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select

from news_aggregator.models.database import Article, User, get_engine, get_session_factory, session_scope
from news_aggregator.config.settings import Settings

logger = logging.getLogger(__name__)


class Recommender:
    def __init__(self, settings: Settings) -> None:
        self._engine = get_engine(settings.database_url)
        self._session_factory = get_session_factory(self._engine)
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def get_recent_articles(self, hours: int = 24) -> List[Article]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        with session_scope(self._session_factory) as session:
            stmt = select(Article).where(Article.published_at >= cutoff)
            return list(session.scalars(stmt).all())

    def rank(self, user: User, top_k: int = 10) -> List[Article]:
        articles = self.get_recent_articles()

        if not articles:
            return []

        texts = [
            (a.title or "") + " " + (a.summary or "")
            for a in articles
        ]

        tfidf_matrix = self.vectorizer.fit_transform(texts)

        user_prefs = " ".join(user.get_preferences().get("topics", []))
        if not user_prefs:
            user_prefs = "general news"

        user_vec = self.vectorizer.transform([user_prefs])

        similarity_scores = cosine_similarity(user_vec, tfidf_matrix).flatten()

        recency_scores = np.array([
            self._recency_score(a.published_at) for a in articles
        ])

        source_scores = np.array([
            self._source_weight(a.source) for a in articles
        ])

        final_scores = (
            0.6 * similarity_scores +
            0.3 * recency_scores +
            0.1 * source_scores
        )

        ranked_indices = np.argsort(final_scores)[::-1]

        return [articles[i] for i in ranked_indices[:top_k]]

    def _recency_score(self, published_at):
        if not published_at:
            return 0.0

        # FIX: make datetime timezone-aware if naive
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        age_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        return max(0.0, 1 - age_hours / 24)

    def _source_weight(self, source):
        if not source:
            return 0.5

        preferred_sources = ["Reuters", "BBC", "NYTimes"]
        return 1.0 if source in preferred_sources else 0.6