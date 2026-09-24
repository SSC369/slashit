"""Shared test fixtures."""

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.db import create_engine, create_session_factory
from app.core.jobs import procrastinate_app
from app.core.settings import Settings, get_settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Real settings. The database tests need a real database."""
    return get_settings()


@pytest.fixture
async def client(
    settings: Settings,
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    """An async client speaking to the app in-process, no network.

    httpx's ASGITransport does not run the lifespan, so the state the lifespan
    would populate is set here from the same fixtures. Adding asgi-lifespan just
    for this would be a dependency to carry for one line.
    """
    app = create_app(settings)
    app.state.engine = engine
    app.state.session_factory = session_factory
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    eng = create_engine(settings)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@pytest.fixture
async def two_users(engine: AsyncEngine) -> AsyncIterator[tuple[uuid.UUID, uuid.UUID]]:
    """Two real rows in auth.users, removed afterwards.

    Real rows are required because ai_usage carries a foreign key to auth.users,
    per decision AD-9: there is no mirrored users table to fake against.
    """
    user_a, user_b = uuid.uuid4(), uuid.uuid4()
    async with engine.begin() as conn:
        for user_id in (user_a, user_b):
            await conn.execute(
                text(
                    "INSERT INTO auth.users (id, email, instance_id) "
                    "VALUES (:id, :email, '00000000-0000-0000-0000-000000000000')"
                ),
                {"id": user_id, "email": f"{user_id}@rls-test.invalid"},
            )
    try:
        yield user_a, user_b
    finally:
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM auth.users WHERE id = ANY(:ids)"),
                {"ids": [user_a, user_b]},
            )


@pytest.fixture
async def job_queue(
    engine: AsyncEngine, two_users: tuple[uuid.UUID, uuid.UUID]
) -> AsyncIterator[None]:
    """The real job queue, open as the API's lifespan opens it. Jobs the test
    queued for its two users are removed afterwards."""
    locks = [f"tz:{user_id}" for user_id in two_users]
    async with procrastinate_app.open_async():
        try:
            yield
        finally:
            async with engine.begin() as conn:
                # The queue's triggers name its tables unqualified (0020).
                await conn.execute(text("SET LOCAL search_path TO procrastinate"))
                await conn.execute(
                    text(
                        "DELETE FROM procrastinate.procrastinate_jobs "
                        "WHERE queueing_lock = ANY(:locks)"
                    ),
                    {"locks": locks},
                )
