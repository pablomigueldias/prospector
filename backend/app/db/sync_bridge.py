from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from app.config import settings


bridge_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.db_echo,
)

BridgeSession = async_sessionmaker(
    bind=bridge_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def bridge_session():
    session = BridgeSession()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
