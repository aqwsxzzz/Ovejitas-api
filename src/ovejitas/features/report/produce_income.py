"""Allocated produce income per (producer asset, currency).

The bridge between the FIFO draw and profitability_full: an animal's own income
events never include what its eggs sold for, because that money is booked on the
pool. This supplies the missing half.

The window is applied to the *result*, never to the input. A FIFO draw depends
on every deposit and withdrawal that came before it, so filtering the ledger to
the window would re-price history rather than report it.
"""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.farm.timezone import farm_timezone
from ovejitas.features.report.produce_fifo import Allocation, draw
from ovejitas.features.report.produce_ledger import (
    load_baskets,
    load_outflows,
    pool_ids,
)


async def allocations_for_farm(db: AsyncSession, farm_id: int) -> list[Allocation]:
    """Every per-producer allocation across every pool in the farm."""
    tz = await farm_timezone(db, farm_id)
    allocations: list[Allocation] = []
    for pool_id in await pool_ids(db, farm_id):
        baskets = await load_baskets(db, pool_id, tz)
        outflows = await load_outflows(db, pool_id)
        allocations.extend(draw(baskets, outflows).allocations)
    return allocations


def income_by_producer_currency(
    allocations: list[Allocation],
    date_from: datetime | None,
    date_to: datetime | None,
) -> dict[tuple[int, str], Decimal]:
    """Sum sale income per (producer, currency), bounded to the window.

    Keyed to match feed_cost_by_consumer so profitability_full can merge the two
    without reshaping either.
    """
    totals: dict[tuple[int, str], Decimal] = defaultdict(lambda: Decimal(0))
    for a in allocations:
        if not a.is_sale or a.currency is None or a.amount == 0:
            continue
        if date_from is not None and a.occurred_at < date_from:
            continue
        if date_to is not None and a.occurred_at > date_to:
            continue
        totals[(a.producer_asset_id, a.currency)] += a.amount
    return dict(totals)
