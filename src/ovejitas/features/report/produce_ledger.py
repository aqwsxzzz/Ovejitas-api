"""Reading a produce pool's history: the lots that filled it and the outflows
that drained it. Loading only — the FIFO draw itself lives in produce_fifo.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType, InventoryAdjustment
from ovejitas.features.harvest.models import ProduceLot

_SALE_SOURCE = "material_sale"


@dataclass
class Basket:
    """One calendar day's harvests into a pool, and who contributed them.

    The day is the lot grain: eggs gathered from three coops on the same morning
    land in one basket, so the order they were recorded in must not change
    anyone's share of a later sale.
    """

    day: date
    contributions: dict[int, Decimal] = field(default_factory=dict)

    @property
    def remaining(self) -> Decimal:
        return sum(self.contributions.values(), Decimal(0))


@dataclass(frozen=True)
class Outflow:
    """Stock leaving a pool, with whatever money it earned.

    ``amount`` is zero for a draw that earned nothing — waste, spoilage, or a
    reset — which still consumes lots so the producers see what they made but
    never sold.
    """

    occurred_at: datetime
    quantity: Decimal
    amount: Decimal
    currency: str | None
    is_sale: bool
    is_reset: bool


async def load_baskets(db: AsyncSession, produce_asset_id: int, tz: ZoneInfo) -> list[Basket]:
    """Every lot in the pool, oldest first, merged into per-day baskets.

    Days are the farm's *local* calendar days: a harvest stored at 23:30
    Montevideo time belongs to that day's basket, not the next UTC day's.
    ``occurred_at`` comes back UTC-aware, so shifting it into ``tz`` before
    taking the date is what makes the grain match the farmer's day.

    Never date-bounded: a FIFO draw depends on everything deposited before it,
    so a window applied here would silently re-price history.
    """
    stmt = (
        select(ProduceLot.occurred_at, ProduceLot.producer_asset_id, ProduceLot.quantity)
        .where(ProduceLot.produce_asset_id == produce_asset_id)
        .order_by(ProduceLot.occurred_at.asc(), ProduceLot.id.asc())
    )
    baskets: dict[date, Basket] = {}
    for occurred_at, producer_asset_id, quantity in (await db.execute(stmt)).all():
        day = occurred_at.astimezone(tz).date()
        basket = baskets.setdefault(day, Basket(day=day))
        basket.contributions[producer_asset_id] = basket.contributions.get(
            producer_asset_id, Decimal(0)
        ) + Decimal(quantity)
    return [baskets[day] for day in sorted(baskets)]


async def load_outflows(db: AsyncSession, produce_asset_id: int) -> list[Outflow]:
    """Every stock movement out of the pool, oldest first, priced where it sold.

    A sale's amount lives on a separate income event, reachable only through the
    ``income_event_id`` the sale action writes onto the decrement — income
    events carry no quantity, so nothing else pairs one sale to one price.
    """
    stmt = (
        select(
            Event.occurred_at,
            Event.quantity,
            Event.adjustment,
            Event.payload,
        )
        .where(
            Event.asset_id == produce_asset_id,
            Event.type == EventType.INVENTORY,
            Event.adjustment.in_([InventoryAdjustment.DECREMENT, InventoryAdjustment.RESET]),
        )
        .order_by(Event.occurred_at.asc(), Event.id.asc())
    )
    rows = (await db.execute(stmt)).all()
    prices = await _income_by_event_id(db, {r.payload.get("income_event_id") for r in rows})

    outflows: list[Outflow] = []
    for occurred_at, quantity, adjustment, payload in rows:
        amount, currency = prices.get(payload.get("income_event_id"), (Decimal(0), None))
        outflows.append(
            Outflow(
                occurred_at=occurred_at,
                quantity=Decimal(quantity or 0),
                amount=amount,
                currency=currency,
                is_sale=payload.get("source") == _SALE_SOURCE,
                is_reset=adjustment is InventoryAdjustment.RESET,
            )
        )
    return outflows


async def _income_by_event_id(
    db: AsyncSession, event_ids: set[int | None]
) -> dict[int, tuple[Decimal, str | None]]:
    from ovejitas.features.currency.models import Currency

    ids = {i for i in event_ids if i is not None}
    if not ids:
        return {}
    stmt = (
        select(Event.id, Event.amount, Currency.code)
        .join(Currency, Currency.id == Event.currency_id)
        .where(Event.id.in_(ids), Event.type == EventType.INCOME)
    )
    return {
        eid: (Decimal(amount or 0), code) for eid, amount, code in (await db.execute(stmt)).all()
    }


async def pool_ids(db: AsyncSession, farm_id: int) -> list[int]:
    """Every produce asset in the farm that has ever received a lot."""
    stmt = (
        select(ProduceLot.produce_asset_id)
        .join(Asset, Asset.id == ProduceLot.produce_asset_id)
        .where(Asset.farm_id == farm_id)
        .distinct()
    )
    return list((await db.execute(stmt)).scalars().all())


def contributions_by_producer(baskets: list[Basket]) -> dict[int, Decimal]:
    """Total quantity each producer ever put into the pool."""
    produced: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    for basket in baskets:
        for producer_id, quantity in basket.contributions.items():
            produced[producer_id] += quantity
    return dict(produced)
