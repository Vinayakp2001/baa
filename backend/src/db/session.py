"""Async SQLAlchemy session factory and FastAPI dependency injection.

Uses asyncpg driver via the postgresql+asyncpg DSN from DATABASE_URL.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings

# Engine: pool_pre_ping keeps idle connections healthy across container restarts
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

# Session factory — expire_on_commit=False avoids lazy-load errors after commit
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a scoped async database session.

    Usage::

        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
