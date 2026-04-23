from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from ovejitas.core.db import get_db
from ovejitas.main import app
from ovejitas.models import Base
from tests.factories import bind_factories

ADMIN_URL = "postgresql+asyncpg://ovejitas:ovejitas@db:5432/ovejitas"
TEST_URL = "postgresql+asyncpg://ovejitas:ovejitas@db:5432/ovejitas_test"


async def _ensure_test_database() -> None:
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'ovejitas_test'")
        )
        if exists.scalar() is None:
            await conn.execute(text("CREATE DATABASE ovejitas_test"))
    await admin.dispose()


@pytest.fixture
async def engine() -> AsyncGenerator[AsyncEngine]:
    await _ensure_test_database()
    test_engine = create_async_engine(TEST_URL, poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield test_engine
    finally:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        bind_factories(session)
        yield session


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
