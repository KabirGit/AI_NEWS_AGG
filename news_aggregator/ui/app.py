"""Streamlit UI.

Phase 0 skeleton: implementation will follow in Phase 8.
"""
from __future__ import annotations
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


import streamlit as st
from sqlalchemy import select

from news_aggregator.config.settings import Settings
from news_aggregator.models.database import (
    User,
    get_session_factory,
    init_db,
    session_scope,
)
from news_aggregator.recommender.engine import Recommender
from news_aggregator.summarizer.summarizer import Summarizer


st.set_page_config(page_title="AI News Aggregator", layout="wide")


@st.cache_resource
def _get_db_session_factory():
    settings = Settings.load()
    engine = init_db(settings)
    return get_session_factory(engine)


def main():
    st.title("🧠 AI Personalized News Aggregator")

    settings = Settings.load()

    session_factory = _get_db_session_factory()

    recommender = Recommender(settings)
    summarizer = Summarizer()

    # --- USER INPUT ---
    st.sidebar.header("User Settings")

    email = st.sidebar.text_input("Enter Email")

    topics = st.sidebar.multiselect(
        "Select Topics",
        ["technology", "finance", "sports", "politics", "health", "ai"],
    )

    if st.sidebar.button("Save Preferences"):
        if not email:
            st.error("Email required")
        else:
            with session_scope(session_factory) as session:
                user = session.scalar(select(User).where(User.email == email))

                if not user:
                    user = User(email=email)
                    session.add(user)

                user.set_preferences({"topics": topics})

            st.success("Preferences saved")

    # --- GENERATE NEWS ---
    if st.button("Generate Today's News"):
        if not email:
            st.error("Enter email first")
            return

        with session_scope(session_factory) as session:
            user = session.scalar(select(User).where(User.email == email))

            if not user:
                st.error("User not found. Save preferences first.")
                return

        articles = recommender.rank(user)

        st.subheader("📰 Your Top Articles")

        for a in articles:
            summary = summarizer.summarize(a.summary or a.content)

            with st.container():
                st.markdown(f"### [{a.title}]({a.link})")
                st.markdown(summary)
                st.caption(f"Source: {a.source}")
                st.markdown("---")


if __name__ == "__main__":
    main()