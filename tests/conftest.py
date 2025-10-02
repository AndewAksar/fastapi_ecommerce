import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# Ensure models are imported so that metadata is populated before creating tables.
from app.models import category as _category  # noqa: F401
from app.models import products as _products  # noqa: F401
from app.models import reviews as _reviews  # noqa: F401
from app.models import user as _user  # noqa: F401

from app.backend.db import Base, engine, async_session_maker

import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session