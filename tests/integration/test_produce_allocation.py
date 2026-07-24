"""End-to-end: harvest into a shared pool, sell the pool, and see the money
land back on the animals that made it.

The FIFO arithmetic is pinned in tests/unit/test_produce_fifo.py. These tests
check the wiring: that harvests record lots, that a sale's income is reachable
from its stock movement, and that both reports read the same allocation.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser

EGGS = {"name": "Huevos", "kind": "produce", "mode": "aggregated"}
FLOCK = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}


def farm_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}"


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def reports_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports"


async def _asset(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _category(client: AsyncClient, authed: AuthedUser) -> int:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/event-categories",
        headers=authed.headers,
        json={"type": "production", "name": "Huevos", "unit": "unit"},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _harvest(
    client: AsyncClient,
    authed: AuthedUser,
    producer_id: int,
    pool_id: int,
    category_id: int,
    quantity: str,
    occurred_at: str,
) -> None:
    resp = await client.post(
        f"{assets_url(authed.farm_id)}/{producer_id}/harvests",
        headers=authed.headers,
        json={
            "quantity": quantity,
            "unit": "unit",
            "produce_asset_id": pool_id,
            "category_id": category_id,
            "occurred_at": occurred_at,
        },
    )
    assert resp.status_code == 201, resp.text


async def _sell(
    client: AsyncClient,
    authed: AuthedUser,
    pool_id: int,
    quantity: str,
    amount: str,
    occurred_at: str,
) -> None:
    resp = await client.post(
        f"{assets_url(authed.farm_id)}/{pool_id}/sales",
        headers=authed.headers,
        json={
            "quantity": quantity,
            "unit": "unit",
            "amount": amount,
            "occurred_at": occurred_at,
        },
    )
    assert resp.status_code == 201, resp.text


async def _outcome(client: AsyncClient, authed: AuthedUser) -> dict[int, dict[str, object]]:
    resp = await client.get(
        f"{reports_url(authed.farm_id)}/produce-outcome", headers=authed.headers
    )
    assert resp.status_code == 200, resp.text
    return {row["producer_asset_id"]: row for row in resp.json()["data"]}


async def _profitability_full(
    client: AsyncClient, authed: AuthedUser
) -> dict[int, dict[str, object]]:
    resp = await client.get(
        f"{reports_url(authed.farm_id)}/profitability-full", headers=authed.headers
    )
    assert resp.status_code == 200, resp.text
    return {row["asset_id"]: row for row in resp.json()["data"]}


class TestPooledSaleAllocation:
    async def test_sale_income_splits_across_contributors_by_share(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        pool = await _asset(client, authed_user, EGGS)
        coop_a = await _asset(client, authed_user, {**FLOCK, "name": "Coop A"})
        coop_b = await _asset(client, authed_user, {**FLOCK, "name": "Coop B"})
        category = await _category(client, authed_user)

        await _harvest(client, authed_user, coop_a, pool, category, "60", "2026-07-01T08:00:00Z")
        await _harvest(client, authed_user, coop_b, pool, category, "40", "2026-07-01T10:00:00Z")
        await _sell(client, authed_user, pool, "100", "200.00", "2026-07-02T12:00:00Z")

        rows = await _outcome(client, authed_user)

        assert rows[coop_a]["income_total"] == "120.00"
        assert rows[coop_b]["income_total"] == "80.00"
        assert rows[coop_a]["sold"] == "60.000000"
        assert rows[coop_b]["sold"] == "40.000000"

    async def test_allocated_income_reaches_profitability_full(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        pool = await _asset(client, authed_user, EGGS)
        coop = await _asset(client, authed_user, {**FLOCK, "name": "Coop A"})
        category = await _category(client, authed_user)

        await _harvest(client, authed_user, coop, pool, category, "50", "2026-07-01T08:00:00Z")
        await _sell(client, authed_user, pool, "50", "125.00", "2026-07-02T12:00:00Z")

        rows = await _profitability_full(client, authed_user)

        # The flock books no income of its own — every peso came from the pool.
        assert rows[coop]["income_total"] == "0"
        assert rows[coop]["allocated_produce_income"] == "125.00"
        assert rows[coop]["net_incl_materials"] == "125.00"
        # The pool is a material asset and stays excluded, so nothing is counted
        # twice.
        assert pool not in rows

    async def test_unsold_production_earns_nothing_but_is_still_reported(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        pool = await _asset(client, authed_user, EGGS)
        coop = await _asset(client, authed_user, {**FLOCK, "name": "Coop A"})
        category = await _category(client, authed_user)

        await _harvest(client, authed_user, coop, pool, category, "30", "2026-07-01T08:00:00Z")

        rows = await _outcome(client, authed_user)

        assert rows[coop]["produced"] == "30"
        assert rows[coop]["sold"] == "0"
        assert rows[coop]["income_total"] == "0"
        assert rows[coop]["currency"] is None

    async def test_second_pool_is_allocated_independently(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        eggs = await _asset(client, authed_user, EGGS)
        feathers = await _asset(client, authed_user, {**EGGS, "name": "Plumas"})
        coop = await _asset(client, authed_user, {**FLOCK, "name": "Coop A"})
        category = await _category(client, authed_user)

        await _harvest(client, authed_user, coop, eggs, category, "10", "2026-07-01T08:00:00Z")
        await _harvest(client, authed_user, coop, feathers, category, "5", "2026-07-01T09:00:00Z")
        await _sell(client, authed_user, eggs, "10", "50.00", "2026-07-02T12:00:00Z")

        resp = await client.get(
            f"{reports_url(authed_user.farm_id)}/produce-outcome",
            headers=authed_user.headers,
            params={"produce_asset_id": feathers},
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["produce_asset_id"] == feathers
        assert data[0]["income_total"] == "0"


class TestLocalDayBasketGrain:
    # Two harvests at the same two instants — 23:00Z Jul 1 and 01:00Z Jul 2 —
    # straddle UTC midnight. In Montevideo (UTC-3) both are the evening of Jul 1
    # (20:00 and 22:00 local), so which farm tz is set is the only thing that
    # decides whether they share a basket. A sale of 50 from a 60/40 pool draws
    # 30/20 when they share one, or drains the older basket first when they
    # don't — a clean 60/40 vs 100/0 split.
    _COOP_A_AT = "2026-07-01T23:00:00Z"
    _COOP_B_AT = "2026-07-02T01:00:00Z"
    _SALE_AT = "2026-07-03T15:00:00Z"

    async def _run(self, client: AsyncClient, authed: AuthedUser) -> dict[int, dict[str, object]]:
        pool = await _asset(client, authed, EGGS)
        coop_a = await _asset(client, authed, {**FLOCK, "name": "Coop A"})
        coop_b = await _asset(client, authed, {**FLOCK, "name": "Coop B"})
        category = await _category(client, authed)
        await _harvest(client, authed, coop_a, pool, category, "60", self._COOP_A_AT)
        await _harvest(client, authed, coop_b, pool, category, "40", self._COOP_B_AT)
        await _sell(client, authed, pool, "50", "100.00", self._SALE_AT)
        rows = await _outcome(client, authed)
        return {"a": rows.get(coop_a, {}), "b": rows.get(coop_b, {})}  # type: ignore[dict-item]

    async def test_local_day_farm_shares_one_basket(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.patch(
            farm_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"timezone": "America/Montevideo"},
        )
        assert resp.status_code == 200, resp.text

        rows = await self._run(client, authed_user)

        # One Montevideo-day basket of 60/40: the sale of 50 draws 30/20.
        assert rows["a"]["income_total"] == "60.00"
        assert rows["b"]["income_total"] == "40.00"

    async def test_utc_farm_splits_across_two_baskets(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # The default UTC farm reads the very same instants as two days, so the
        # older basket (coop A, 60) is drained first and takes the whole sale.
        rows = await self._run(client, authed_user)

        assert rows["a"]["income_total"] == "100.00"
        assert not rows["b"] or rows["b"]["income_total"] == "0"


class TestSaleCorrelation:
    async def test_sale_decrement_points_at_the_income_it_earned(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # Without this link nothing pairs one sale's quantity to one sale's
        # amount, and the allocation has no per-sale unit price to work from.
        pool = await _asset(client, authed_user, EGGS)
        coop = await _asset(client, authed_user, {**FLOCK, "name": "Coop A"})
        category = await _category(client, authed_user)
        await _harvest(client, authed_user, coop, pool, category, "20", "2026-07-01T08:00:00Z")
        await _sell(client, authed_user, pool, "5", "12.50", "2026-07-02T12:00:00Z")

        resp = await client.get(
            f"{assets_url(authed_user.farm_id)}/{pool}/events",
            headers=authed_user.headers,
            params={"type": "inventory", "adjustment": "decrement"},
        )

        assert resp.status_code == 200, resp.text
        decrement = resp.json()["data"][0]
        assert decrement["payload"]["source"] == "material_sale"
        assert decrement["payload"]["income_event_id"] is not None


class TestTwoSalesAtDifferentPrices:
    async def test_each_sale_prices_only_the_stock_it_took(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        pool = await _asset(client, authed_user, EGGS)
        coop_a = await _asset(client, authed_user, {**FLOCK, "name": "Coop A"})
        coop_b = await _asset(client, authed_user, {**FLOCK, "name": "Coop B"})
        category = await _category(client, authed_user)

        # Day 1 is all coop A; day 2 all coop B. The first sale drains day 1
        # cheaply, the second takes day 2 at double the price — so the price
        # difference must land entirely on coop B.
        await _harvest(client, authed_user, coop_a, pool, category, "100", "2026-07-01T08:00:00Z")
        await _harvest(client, authed_user, coop_b, pool, category, "100", "2026-07-02T08:00:00Z")
        await _sell(client, authed_user, pool, "100", "100.00", "2026-07-03T12:00:00Z")
        await _sell(client, authed_user, pool, "100", "200.00", "2026-07-04T12:00:00Z")

        rows = await _outcome(client, authed_user)

        assert rows[coop_a]["income_total"] == "100.00"
        assert rows[coop_b]["income_total"] == "200.00"
