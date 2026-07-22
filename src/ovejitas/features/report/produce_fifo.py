"""The FIFO draw — deriving who earned what from a pooled produce sale.

Once eggs from three coops are in one basket they are indistinguishable, so no
per-producer income is ever observed; it can only be allocated. This module is
that allocation, and it is the only definition of it: nothing is stored, so a
corrected harvest simply changes the answer the next time it is asked.

The rule, in full: consume baskets oldest first; within each basket split the
consumed quantity in proportion to what each producer put in it; price every
consumed unit at that outflow's own unit price. Never sequentially (never "fill
the first coop's share first"), never round-robin — proportional-within-basket
is what makes the result independent of the order harvests were recorded in.

Pure computation over the loaded ledger; the reads live in produce_ledger.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from ovejitas.features.report.produce_ledger import Basket, Outflow
from ovejitas.features.report.produce_rounding import apportion_money, apportion_quantity


@dataclass(frozen=True)
class Allocation:
    """One producer's share of one outflow."""

    producer_asset_id: int
    occurred_at: datetime
    quantity: Decimal
    amount: Decimal
    currency: str | None
    is_sale: bool


@dataclass
class PoolDraw:
    allocations: list[Allocation]
    # Stock that left the pool without a lot behind it — a manual inventory
    # increment, or stock carried over a reset. Surfaced rather than dropped so
    # a report never implies the producers earned money that was not theirs.
    unattributed_quantity: Decimal = Decimal(0)
    unattributed_amount: Decimal = Decimal(0)


def draw(baskets: list[Basket], outflows: list[Outflow]) -> PoolDraw:
    """Walk every outflow against the baskets, oldest first."""
    remaining = [dict(b.contributions) for b in baskets]
    result = PoolDraw(allocations=[])
    cursor = 0

    for outflow in outflows:
        if outflow.is_reset:
            # A reset declares a new on-hand truth. Whatever the baskets still
            # claim is no longer what is in the pool, so attribution restarts.
            remaining = []
            cursor = 0
            continue
        cursor, taken = _consume(remaining, cursor, outflow.quantity)
        _record(result, outflow, taken)
    return result


def _consume(
    remaining: list[dict[int, Decimal]], cursor: int, wanted: Decimal
) -> tuple[int, dict[int, Decimal]]:
    """Draw ``wanted`` from the baskets at and after ``cursor``, proportionally
    within each. Returns the new cursor and what each producer gave up."""
    taken: dict[int, Decimal] = {}
    outstanding = wanted
    while outstanding > 0 and cursor < len(remaining):
        basket = remaining[cursor]
        available = sum(basket.values(), Decimal(0))
        if available <= 0:
            cursor += 1
            continue
        portion = min(outstanding, available)
        producers = sorted(basket)
        shares = apportion_quantity([basket[p] for p in producers], portion)
        for producer_id, share in zip(producers, shares, strict=True):
            basket[producer_id] -= share
            taken[producer_id] = taken.get(producer_id, Decimal(0)) + share
        outstanding -= portion
        if portion == available:
            cursor += 1
    return cursor, taken


def _record(result: PoolDraw, outflow: Outflow, taken: dict[int, Decimal]) -> None:
    """Price one outflow's draw and append it to the running result."""
    attributed = sum(taken.values(), Decimal(0))
    shortfall = outflow.quantity - attributed

    # Split the money between what the baskets covered and what they did not,
    # before splitting the covered part across producers. Two exact splits keep
    # every cent of the sale accounted for.
    covered_amount, uncovered_amount = apportion_money([attributed, shortfall], outflow.amount)
    if shortfall > 0:
        result.unattributed_quantity += shortfall
        result.unattributed_amount += uncovered_amount

    producers = sorted(taken)
    amounts = apportion_money([taken[p] for p in producers], covered_amount)
    for producer_id, amount in zip(producers, amounts, strict=True):
        result.allocations.append(
            Allocation(
                producer_asset_id=producer_id,
                occurred_at=outflow.occurred_at,
                quantity=taken[producer_id],
                amount=amount,
                currency=outflow.currency,
                is_sale=outflow.is_sale,
            )
        )
