import asyncio
import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from ovejitas.core.db import get_db
from ovejitas.main import app
from ovejitas.models import Base
from tests.factories import bind_factories

ADMIN_URL = "postgresql+asyncpg://ovejitas:ovejitas@db:5433/ovejitas"


def _worker_id() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def _test_db_name() -> str:
    return f"ovejitas_test_{_worker_id()}"


def _test_url() -> str:
    return f"postgresql+asyncpg://ovejitas:ovejitas@db:5433/{_test_db_name()}"


# Bcrypt at default rounds (12) costs ~250ms per hash. Drop to 4 for tests.
_original_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4, prefix=b"2b": _original_gensalt(rounds=4, prefix=prefix)  # type: ignore[assignment]


async def _setup_schema() -> None:
    db_name = _test_db_name()
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n").bindparams(n=db_name)
        )
        if exists.scalar() is None:
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await admin.dispose()
    setup_engine = create_async_engine(_test_url())
    async with setup_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await setup_engine.dispose()


asyncio.run(_setup_schema())


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine]:
    test_engine = create_async_engine(_test_url())
    try:
        yield test_engine
    finally:
        await test_engine.dispose()


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    """Each test runs inside an outer transaction that gets rolled back.

    The app's session.commit() becomes a SAVEPOINT release (via
    join_transaction_mode='create_savepoint'), so endpoint code sees normal
    commit semantics, but no data persists between tests. This avoids both
    per-test engine creation and TRUNCATE.
    """
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    bind_factories(session)
    try:
        yield session
    finally:
        await session.close()
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            yield http
    finally:
        app.dependency_overrides.clear()


@dataclass(slots=True)
class AuthedUser:
    user_id: int
    farm_id: int
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


async def _register(client: AsyncClient, email: str) -> AuthedUser:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": email.split("@")[0], "password": "password123"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = me.json()
    return AuthedUser(
        user_id=body["user"]["id"],
        farm_id=body["memberships"][0]["farm_id"],
        token=token,
    )


@pytest.fixture
async def authed_user(client: AsyncClient) -> AuthedUser:
    return await _register(client, "default@example.com")


@pytest.fixture
def register_user(
    client: AsyncClient,
) -> Callable[[str], Awaitable[AuthedUser]]:
    async def _factory(email: str) -> AuthedUser:
        return await _register(client, email)

    return _factory
