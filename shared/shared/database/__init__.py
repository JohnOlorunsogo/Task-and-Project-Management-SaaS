"""Async SQLAlchemy session factory."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


class DatabaseSessionManager:
    """Manages async database engine and session factory."""

    def __init__(self) -> None:
        self.engine = None
        self.session_factory = None

    def init(self, database_url: str, echo: bool = False) -> None:
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncSession:
        if not self.session_factory:
            raise RuntimeError("DatabaseSessionManager not initialized")
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global instance — each service calls db_manager.init(url) at startup
db_manager = DatabaseSessionManager()
