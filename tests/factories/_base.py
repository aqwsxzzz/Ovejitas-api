from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.asyncio import AsyncSession


class BaseFactory(SQLAlchemyFactory):
    """Shared base so every factory inherits a single session + defaults.

    Subclasses set `__model__`; adding a new factory = one file under
    tests/factories/ plus an export line in __init__.py.
    """

    __is_base_factory__ = True
    __set_primary_key__ = False
    __set_foreign_keys__ = False


def bind_factories(session: AsyncSession) -> None:
    """Bind one session to every factory. Called once per test by the fixture."""
    BaseFactory.__async_session__ = session
