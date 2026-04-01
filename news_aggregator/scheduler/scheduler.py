"""Cron-compatible scheduler entrypoints.

Phase 0 skeleton: implementation will follow in Phase 7.
"""

from __future__ import annotations

import logging

from news_aggregator.config.settings import Settings
from news_aggregator.ingestion.rss_fetcher import fetch_and_ingest
from news_aggregator.recommender.engine import Recommender
from news_aggregator.summarizer.summarizer import Summarizer
from news_aggregator.email_service.email_sender import EmailSender
from news_aggregator.models.database import User, get_engine, get_session_factory, session_scope
from sqlalchemy import select

logger = logging.getLogger(__name__)

import time
import os

def run_daily_pipeline():
    print(">>> PIPELINE STARTED <<<")
    settings = Settings.load()

    SEND_EMAILS = os.getenv("SEND_EMAILS", "true").lower() == "true"

    logger.info("Starting pipeline...")

    inserted = fetch_and_ingest(settings)
    logger.info("Inserted %d new articles", inserted)

    recommender = Recommender(settings)
    summarizer = Summarizer()
    email_sender = EmailSender()

    engine = get_engine(settings.database_url)
    session_factory = get_session_factory(engine)

    with session_scope(session_factory) as session:
        users = session.scalars(select(User)).all()

        for user in users:
            articles = recommender.rank(user)

            for a in articles:
                a.summary = summarizer.summarize(a.summary or a.content)

            if SEND_EMAILS:
                print("📧 Sending email to:", user.email)
                email_sender.send_digest(user, articles)
            else:
                print("🚫 Email sending disabled")

    logger.info("Pipeline completed.")


if __name__ == "__main__":
    while True:
        run_daily_pipeline()
        print("😴 Sleeping for 24 hours...")
        time.sleep(86400)