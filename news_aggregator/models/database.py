"""SQLAlchemy ORM models and DB session management."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import json
import logging
from typing import Any, Generator, Iterable, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from news_aggregator.config.settings import Settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    # Practical additions for a news aggregator (helps dedupe + UI/email).
    link: Mapped[str | None] = mapped_column(String(2048), nullable=True, unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="article", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Article(id={self.id!r}, title={self.title!r}, published_at={self.published_at!r}, source={self.source!r})"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)

    # Stored as JSON text for SQLite portability.
    preferences: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def set_preferences(self, prefs: dict[str, Any]) -> None:
        self.preferences = json.dumps(prefs, ensure_ascii=False)

    def get_preferences(self) -> dict[str, Any]:
        try:
            parsed = json.loads(self.preferences)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"


class Interaction(Base):
    __tablename__ = "interactions"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_interactions_user_article"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="interactions")
    article: Mapped[Article] = relationship(back_populates="interactions")

    def __repr__(self) -> str:
        return f"Interaction(id={self.id!r}, user_id={self.user_id!r}, article_id={self.article_id!r}, timestamp={self.timestamp!r})"


def get_engine(database_url: str, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine."""
    # future=True is default in SQLAlchemy 2.x; left implicit.
    return create_engine(database_url, echo=echo)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a configured session factory."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """Provide a transactional scope around operations."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(settings: Settings, *, echo_sql: bool = False) -> Engine:
    """Initialize the database schema and return the engine."""
    engine = get_engine(settings.database_url, echo=echo_sql)
    Base.metadata.create_all(engine)
    logger.info("Database initialized.")
    return engine


