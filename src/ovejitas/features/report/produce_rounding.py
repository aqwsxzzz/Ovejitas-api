"""Largest-remainder apportionment.

Rounding each share independently invents or destroys value: three producers
splitting 10.00 evenly get 3.33 each and a cent goes missing. Largest remainder
floors every share to the smallest representable unit, then hands the leftover
units one at a time to whoever was rounded down hardest — so the parts always
sum to exactly the total. Pure computation; no I/O.
"""

from collections.abc import Sequence
from decimal import Decimal

# Event.amount is NUMERIC(14, 2) — the cent is the smallest bookable unit.
_MONEY = Decimal("0.01")
# Quantity is an unconstrained NUMERIC. This is fine enough that a split of
# whole eggs or litres stays exact, and coarse enough to stay away from the
# Decimal context's significant-digit limit.
_QUANTITY = Decimal("0.000001")


def _apportion(weights: Sequence[Decimal], total: Decimal, minor: Decimal) -> list[Decimal]:
    if not weights:
        return []
    weight_sum = sum(weights, Decimal(0))
    if weight_sum <= 0 or total == 0:
        return [minor * 0 for _ in weights]

    minor_total = int((total / minor).to_integral_value())
    exact = [Decimal(minor_total) * w / weight_sum for w in weights]
    floors = [int(e // 1) for e in exact]
    leftover = minor_total - sum(floors)

    # Hand the leftover units to the largest fractional parts. Index breaks ties
    # so the same input always produces the same split.
    order = sorted(range(len(weights)), key=lambda i: (-(exact[i] % 1), i))
    for i in order[:leftover]:
        floors[i] += 1
    return [Decimal(f) * minor for f in floors]


def apportion_money(weights: Sequence[Decimal], total: Decimal) -> list[Decimal]:
    """Split an amount of money across weights, summing to it exactly."""
    return _apportion(weights, total, _MONEY)


def apportion_quantity(weights: Sequence[Decimal], total: Decimal) -> list[Decimal]:
    """Split a quantity across weights, summing to it exactly."""
    return _apportion(weights, total, _QUANTITY)
