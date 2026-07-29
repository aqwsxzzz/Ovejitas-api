"""Produce outcome — what each producer contributed to a pool, and what became
of it: sold, lost, or still sitting in the basket.

Productivity and profitability are different questions and this report refuses
to let one hide the other: quantity produced is reported whether or not any of
it earned money, and quantity lost is reported rather than folded into "not
sold". A farmer wants both numbers.

Windowing note: ``produced`` is bounded by when the harvest happened, while
``sold``/``lost``/``income`` are bounded by when the stock left. FIFO crosses
window edges, so within a narrow window these are not expected to reconcile —
June's eggs are legitimately sold in July.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import Asset
from ovejitas.features.event.types import Unit
from ovejitas.features.farm.timezone import farm_timezone
from ovejitas.features.report.produce_fifo import draw
from ovejitas.features.report.produce_ledger import (
    load_baskets,
    load_outflows,
    pool_ids,
)
from ovejitas.features.report.schemas_produce import (
    ProduceOutcomeQuery,
    ProduceOutcomeReport,
    ProduceOutcomeRow,
)


@dataclass
class _Outcome:
    produced: Decimal = Decimal(0)
    sold: Decimal = Decimal(0)
    lost: Decimal = Decimal(0)
    income: dict[str, Decimal] = field(default_factory=lambda: defaultdict(lambda: Decimal(0)))
    unit: Unit | None = None


def _in_window(value: object, q: ProduceOutcomeQuery) -> bool:
    if q.date_from is not None and value < q.date_from:  # type: ignore[operator]
        return False
    return not (q.date_to is not None and value > q.date_to)  # type: ignore[operator]


async def _pool_unit(db: AsyncSession, pool_id: int) -> Unit | None:
    from ovejitas.features.harvest.models import ProduceLot

    stmt = select(ProduceLot.unit).where(ProduceLot.produce_asset_id == pool_id).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()


async def _accumulate(
    db: AsyncSession, pool_id: int, q: ProduceOutcomeQuery, tz: ZoneInfo
) -> tuple[dict[int, _Outcome], Decimal, Decimal]:
    baskets = await load_baskets(db, pool_id, tz)
    outflows = await load_outflows(db, pool_id)
    result = draw(baskets, outflows)
    unit = await _pool_unit(db, pool_id)

    # basket.day is a local calendar day, so bound the produced side with the
    # window's local days too rather than mixing grains.
    day_from = q.date_from.astimezone(tz).date() if q.date_from is not None else None
    day_to = q.date_to.astimezone(tz).date() if q.date_to is not None else None
    outcomes: dict[int, _Outcome] = defaultdict(_Outcome)
    for basket in baskets:
        for producer_id, quantity in basket.contributions.items():
            if day_from is not None and basket.day < day_from:
                continue
            if day_to is not None and basket.day > day_to:
                continue
            outcome = outcomes[producer_id]
            outcome.produced += quantity
            outcome.unit = unit

    for a in result.allocations:
        if not _in_window(a.occurred_at, q):
            continue
        outcome = outcomes[a.producer_asset_id]
        outcome.unit = outcome.unit or unit
        if a.is_sale:
            outcome.sold += a.quantity
            if a.currency is not None and a.amount:
                outcome.income[a.currency] += a.amount
        else:
            outcome.lost += a.quantity
    return outcomes, result.unattributed_quantity, result.unattributed_amount


async def _asset_names(db: AsyncSession, farm_id: int, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    stmt = select(Asset.id, Asset.name).where(Asset.farm_id == farm_id, Asset.id.in_(ids))
    return {aid: name for aid, name in (await db.execute(stmt)).all()}


def _row(
    producer_id: int, pool_id: int, names: dict[int, str], outcome: _Outcome
) -> ProduceOutcomeRow:
    # Currencies are never summed. One currency fills the row; several leave it
    # null and flagged, so the client asks profitability-full for the money.
    currencies = sorted(outcome.income)
    single = currencies[0] if len(currencies) == 1 else None
    return ProduceOutcomeRow(
        producer_asset_id=producer_id,
        producer_name=names.get(producer_id, ""),
        produce_asset_id=pool_id,
        produce_name=names.get(pool_id, ""),
        unit=outcome.unit or Unit.UNIT,
        produced=outcome.produced,
        sold=outcome.sold,
        lost=outcome.lost,
        currency=single,
        income_total=outcome.income[single] if single else Decimal(0),
        has_other_currency=len(currencies) > 1,
    )


async def produce_outcome(
    db: AsyncSession, farm_id: int, q: ProduceOutcomeQuery
) -> ProduceOutcomeReport:
    tz = await farm_timezone(db, farm_id)
    pools = await pool_ids(db, farm_id)
    if q.produce_asset_id is not None:
        pools = [p for p in pools if p == q.produce_asset_id]

    rows: list[ProduceOutcomeRow] = []
    unattributed_quantity = Decimal(0)
    unattributed_income = Decimal(0)
    ids: set[int] = set()
    collected: list[tuple[int, int, _Outcome]] = []

    for pool_id in pools:
        outcomes, quantity, income = await _accumulate(db, pool_id, q, tz)
        unattributed_quantity += quantity
        unattributed_income += income
        for producer_id, outcome in outcomes.items():
            if q.producer_asset_id is not None and producer_id != q.producer_asset_id:
                continue
            collected.append((producer_id, pool_id, outcome))
            ids.update({producer_id, pool_id})

    names = await _asset_names(db, farm_id, ids)
    rows = [_row(producer_id, pool_id, names, o) for producer_id, pool_id, o in collected]
    rows.sort(key=lambda r: (r.producer_name, r.produce_name))
    return ProduceOutcomeReport(
        data=rows,
        unattributed_quantity=unattributed_quantity,
        unattributed_income=unattributed_income,
    )
