"""Article summarization.

Phase 0 skeleton: implementation will follow in Phase 4.
"""

from __future__ import annotations

import os
import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)


class Summarizer:
    """
    Summarizer with:
    - Default: extractive summarization
    - Optional: OpenAI (if API key present)
    """
    
    def clean_html(self, text: str) -> str:
        import re
        return re.sub(r"<.*?>", "", text)
    
    def __init__(self, use_openai: bool = False) -> None:
        self.use_openai = use_openai and bool(os.getenv("OPENAI_API_KEY"))

    def summarize(self, text, max_sentences: int = 3) -> str:
        if not text:
            return "No summary available."

        text = self.clean_html(text)

        return self._extractive_summary(text, max_sentences)

    def _extractive_summary(self, text: str, max_sentences: int) -> str:
        sentences = text.split(". ")
        if len(sentences) <= max_sentences:
            return text.strip()

        return ". ".join(sentences[:max_sentences]).strip() + "."

    def _openai_summary(self, text: str) -> str:
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Summarize the article in 2-3 concise sentences."},
                {"role": "user", "content": text},
            ],
        )

        return response.choices[0].message.content.strip()