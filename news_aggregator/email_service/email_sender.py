from __future__ import annotations

import os
import logging
import time
from typing import List

import resend

from news_aggregator.models.database import Article, User

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self) -> None:
        api_key = os.getenv("RESEND_API_KEY")
        if not api_key:
            raise ValueError("RESEND_API_KEY not set")

        resend.api_key = api_key
        self.from_email = os.getenv("EMAIL_FROM")
        if not self.from_email:
            raise ValueError("EMAIL_FROM not set")

    def send_digest(self, user: User, articles: List[Article]) -> None:
        content = self._format_digest(articles)

        delays_s = (1.0, 2.0, 4.0)
        last_exc: Exception | None = None
        for i, delay in enumerate(delays_s, start=1):
            try:
                resend.Emails.send(
                    {
                        "from": self.from_email,
                        "to": [user.email],
                        "subject": "Your Daily AI News Digest",
                        "html": content,
                    }
                )
                logger.info("Email sent to %s", user.email)
                return
            except Exception as e:
                last_exc = e
                logger.warning("Email attempt %d/%d failed for %s err=%r", i, len(delays_s), user.email, e)
                time.sleep(delay)
        logger.error("Failed to send email to %s after retries err=%r", user.email, last_exc)

    def _format_digest(self, articles: List[Article]) -> str:
        html = "<h2>Top News for You</h2><ul>"

        for a in articles:
            html += f"""
            <li>
                <a href="{a.link}"><b>{a.title}</b></a><br>
                {a.summary or ''}
            </li><br>
            """

        html += "</ul>"
        return html