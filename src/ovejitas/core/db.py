from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ovejitas.core.config import get_settings

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db"}


def normalize_db_url(raw: str) -> str:
    """Coerce a libpq-style URL into one asyncpg understands.

    Forces the `+asyncpg` driver, drops `sslmode` (asyncpg uses `ssl=`), and
    disables SQLAlchemy's prepared-statement cache (required for PgBouncer
    transaction-mode poolers like Neon's).
    """
    parts = urlsplit(raw)
    scheme = parts.scheme
    if scheme in {"postgres", "postgresql"}:
        scheme = "postgresql+asyncpg"
    query_pairs = [(k, v) for k, v in parse_qsl(parts.query) if k != "sslmode"]
    query_pairs.append(("prepared_statement_cache_size", "0"))
    return urlunsplit(parts._replace(scheme=scheme, query=urlencode(query_pairs)))


def connect_args_for(url: str) -> dict[str, Any]:
    """asyncpg connect args: disable its prepared-stmt cache and require SSL on remote hosts."""
    args: dict[str, Any] = {"statement_cache_size": 0}
    host = urlsplit(url).hostname or ""
    if host not in _LOCAL_HOSTS:
        args["ssl"] = "require"
    return args


def _build_engine() -> AsyncEngine:
    settings = get_settings()
    url = normalize_db_url(settings.database_url)
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=settings.sql_echo,
        connect_args=connect_args_for(url),
    )


engine: AsyncEngine = _build_engine()

session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session
