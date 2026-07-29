"""The allocation rule itself, with no database in the way.

Pooled produce is fungible, so these numbers are the entire definition of who
earned what — worth pinning precisely.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from ovejitas.features.report.produce_fifo import draw
from ovejitas.features.report.produce_ledger import Basket, Outflow
from ovejitas.features.report.produce_rounding import apportion_money

COOP1, COOP2, COOP3 = 1, 2, 3


def _basket(day: int, **contributions: str) -> Basket:
    return Basket(
        day=date(2026, 7, day),
        contributions={int(k[1:]): Decimal(v) for k, v in contributions.items()},
    )


def _sale(day: int, quantity: str, amount: str) -> Outflow:
    return Outflow(
        occurred_at=datetime(2026, 7, day, 12, tzinfo=UTC),
        quantity=Decimal(quantity),
        amount=Decimal(amount),
        currency="UYU",
        is_sale=True,
        is_reset=False,
    )


def _loss(day: int, quantity: str) -> Outflow:
    return Outflow(
        occurred_at=datetime(2026, 7, day, 12, tzinfo=UTC),
        quantity=Decimal(quantity),
        amount=Decimal(0),
        currency=None,
        is_sale=False,
        is_reset=False,
    )


def _income(result: object) -> dict[int, Decimal]:
    totals: dict[int, Decimal] = {}
    for a in result.allocations:  # type: ignore[attr-defined]
        totals[a.producer_asset_id] = totals.get(a.producer_asset_id, Decimal(0)) + a.amount
    return totals


def _quantities(result: object) -> dict[int, Decimal]:
    totals: dict[int, Decimal] = {}
    for a in result.allocations:  # type: ignore[attr-defined]
        totals[a.producer_asset_id] = totals.get(a.producer_asset_id, Decimal(0)) + a.quantity
    return totals


class TestSingleBasket:
    def test_two_sales_at_different_prices_split_by_contribution(self) -> None:
        # The worked example from the request: 500/300/200 in one basket, sold
        # 700 @ 1 then 300 @ 2.
        baskets = [_basket(1, p1="500", p2="300", p3="200")]
        outflows = [_sale(1, "700", "700.00"), _sale(2, "300", "600.00")]

        result = draw(baskets, outflows)

        assert _income(result) == {
            COOP1: Decimal("650.00"),
            COOP2: Decimal("390.00"),
            COOP3: Decimal("260.00"),
        }

    def test_same_day_harvest_order_does_not_change_shares(self) -> None:
        # Baskets are per calendar day precisely so that recording coop3 first
        # cannot hand it the whole of an early sale.
        forward = [_basket(1, p1="500", p2="300", p3="200")]
        reversed_order = [_basket(1, p3="200", p2="300", p1="500")]
        outflows = [_sale(1, "100", "100.00")]

        assert _income(draw(forward, outflows)) == _income(draw(reversed_order, outflows))


class TestFifoAcrossBaskets:
    def test_sale_spanning_two_baskets_uses_each_basket_own_mix(self) -> None:
        # The case the request's example never reaches: the older basket is all
        # coop1, the newer all coop2, and one sale crosses the boundary. A sale
        # of 150 must take 100 from day 1 and 50 from day 2 — not 75/75.
        baskets = [_basket(1, p1="100"), _basket(2, p2="100")]
        outflows = [_sale(3, "150", "300.00")]

        result = draw(baskets, outflows)

        assert _quantities(result) == {COOP1: Decimal("100"), COOP2: Decimal("50")}
        assert _income(result) == {COOP1: Decimal("200.00"), COOP2: Decimal("100.00")}

    def test_oldest_basket_is_exhausted_before_the_next_is_touched(self) -> None:
        baskets = [_basket(1, p1="60", p2="40"), _basket(2, p3="100")]
        outflows = [_sale(3, "50", "50.00")]

        result = draw(baskets, outflows)

        assert _quantities(result) == {COOP1: Decimal("30"), COOP2: Decimal("20")}
        assert COOP3 not in _income(result)

    def test_later_sale_continues_from_the_partially_drawn_basket(self) -> None:
        baskets = [_basket(1, p1="60", p2="40"), _basket(2, p3="100")]
        outflows = [_sale(3, "50", "50.00"), _sale(4, "100", "100.00")]

        result = draw(baskets, outflows)

        # 50 left in basket 1 (30/20), then 50 from basket 2 (all coop3).
        assert _quantities(result) == {
            COOP1: Decimal("60"),
            COOP2: Decimal("40"),
            COOP3: Decimal("50"),
        }


class TestRounding:
    def test_indivisible_split_still_sums_to_the_sale_amount(self) -> None:
        baskets = [_basket(1, p1="1", p2="1", p3="1")]
        outflows = [_sale(1, "3", "10.00")]

        result = draw(baskets, outflows)
        income = _income(result)

        assert sum(income.values()) == Decimal("10.00")
        assert sorted(income.values()) == [Decimal("3.33"), Decimal("3.33"), Decimal("3.34")]

    @pytest.mark.parametrize(
        "weights, total",
        [
            ([Decimal(1), Decimal(1), Decimal(1)], Decimal("0.01")),
            ([Decimal(1), Decimal(2)], Decimal("0.05")),
            ([Decimal("333"), Decimal("333"), Decimal("334")], Decimal("100.00")),
            ([Decimal(7)], Decimal("19.99")),
        ],
        ids=["one cent, three ways", "uneven pair", "near-equal thirds", "single producer"],
    )
    def test_apportion_money_is_exact(self, weights: list[Decimal], total: Decimal) -> None:
        assert sum(apportion_money(weights, total)) == total

    def test_zero_weights_allocate_nothing(self) -> None:
        assert apportion_money([Decimal(0), Decimal(0)], Decimal("10.00")) == [
            Decimal("0.00"),
            Decimal("0.00"),
        ]


class TestZeroRevenueOutflows:
    def test_loss_draws_the_pool_without_booking_income(self) -> None:
        baskets = [_basket(1, p1="50", p2="50")]
        outflows = [_loss(2, "20")]

        result = draw(baskets, outflows)

        assert _quantities(result) == {COOP1: Decimal("10"), COOP2: Decimal("10")}
        assert _income(result) == {COOP1: Decimal("0.00"), COOP2: Decimal("0.00")}

    def test_loss_consumes_stock_a_later_sale_can_no_longer_earn_on(self) -> None:
        baskets = [_basket(1, p1="100")]
        outflows = [_loss(2, "40"), _sale(3, "60", "60.00")]

        result = draw(baskets, outflows)

        assert _quantities(result) == {COOP1: Decimal("100")}
        assert _income(result) == {COOP1: Decimal("60.00")}


class TestUnattributedStock:
    def test_selling_more_than_the_lots_cover_is_reported_not_hidden(self) -> None:
        # Reachable when stock entered by a manual inventory increment rather
        # than a harvest: the money for it belongs to no producer.
        baskets = [_basket(1, p1="10")]
        outflows = [_sale(2, "20", "40.00")]

        result = draw(baskets, outflows)

        assert _income(result) == {COOP1: Decimal("20.00")}
        assert result.unattributed_quantity == Decimal("10")
        assert result.unattributed_amount == Decimal("20.00")

    def test_a_reset_restarts_attribution(self) -> None:
        baskets = [_basket(1, p1="100")]
        reset = Outflow(
            occurred_at=datetime(2026, 7, 2, tzinfo=UTC),
            quantity=Decimal("30"),
            amount=Decimal(0),
            currency=None,
            is_sale=False,
            is_reset=True,
        )
        outflows = [reset, _sale(3, "30", "60.00")]

        result = draw(baskets, outflows)

        # The reset declared a new truth; the old lot no longer describes the
        # pool, so the later sale attributes to nobody.
        assert _income(result) == {}
        assert result.unattributed_quantity == Decimal("30")
