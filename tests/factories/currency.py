from sqlalchemy import select

from ovejitas.features.currency.models import Currency
from tests.factories._base import BaseFactory


class CurrencyFactory(BaseFactory):
    """Caller must pass `farm_id=`. Defaults to a USD row."""

    __model__ = Currency
    code = "USD"
    name = "US Dollar"
    symbol = None
    archived_at = None


async def currency_id_for(farm_id: int, code: str = "USD") -> int:
    """Get-or-create a currency row for (farm, code) and return its id.

    Farms registered via the API already own a USD row; other codes are created
    on demand so tests can build multi-currency ledgers.
    """
    session = BaseFactory.__async_session__
    assert session is not None
    existing = (
        await session.execute(
            select(Currency).where(Currency.farm_id == farm_id, Currency.code == code)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return int(existing.id)
    row = await CurrencyFactory.create_async(farm_id=farm_id, code=code, name=code)
    return int(row.id)
