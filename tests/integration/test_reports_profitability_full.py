from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory, currency_id_for


def reports(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports"


async def _asset(farm_id: int, **kw: object) -> int:
    asset = await AssetFactory.create_async(farm_id=farm_id, **kw)
    return int(asset.id)


async def _material(farm_id: int, name: str = "Feed") -> int:
    return await _asset(farm_id, name=name, kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED)


async def _event(farm_id: int, asset_id: int, user_id: int, **kw: object) -> None:
    when = kw.pop("when", datetime(2026, 4, 10, tzinfo=UTC))
    await EventFactory.create_async(
        farm_id=farm_id, asset_id=asset_id, created_by=user_id, occurred_at=when, **kw
    )


async def _income(farm_id: int, asset_id: int, user_id: int, amount: str, currency: str) -> None:
    await _event(
        farm_id,
        asset_id,
        user_id,
        type=EventType.INCOME,
        amount=Decimal(amount),
        currency_id=await currency_id_for(farm_id, currency),
        quantity=None,
        unit=None,
    )


async def _expense(farm_id: int, asset_id: int, user_id: int, amount: str, currency: str) -> None:
    await _event(
        farm_id,
        asset_id,
        user_id,
        type=EventType.EXPENSE,
        amount=Decimal(amount),
        currency_id=await currency_id_for(farm_id, currency),
        quantity=None,
        unit=None,
    )


async def _buy_material(
    client: AsyncClient,
    authed: AuthedUser,
    material_id: int,
    quantity: str,
    amount: str,
    currency: str | None = None,
) -> None:
    body: dict[str, Any] = {
        "material_asset_id": material_id,
        "occurred_at": "2026-04-01T10:00:00Z",
        "quantity": quantity,
        "unit": "kg",
        "amount": amount,
    }
    if currency is not None:
        body["currency_id"] = await currency_id_for(authed.farm_id, currency)
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/material-purchases",
        headers=authed.headers,
        json=body,
    )
    assert resp.status_code in (200, 201), resp.text


async def _feed(
    client: AsyncClient, authed: AuthedUser, material_id: int, consumer_id: int, quantity: str
) -> None:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/material-consumptions",
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "consumer_asset_id": consumer_id,
            "occurred_at": "2026-04-05T10:00:00Z",
            "quantity": quantity,
            "unit": "kg",
            "reason": "feeding",
        },
    )
    assert resp.status_code in (200, 201), resp.text


async def _full(client: AsyncClient, authed: AuthedUser, **params: str) -> dict[str, Any]:
    resp = await client.get(
        f"{reports(authed.farm_id)}/profitability-full", headers=authed.headers, params=params
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestProfitabilityFull:
    async def test_net_incl_materials_subtracts_feed_and_direct_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        await _buy_material(client, authed_user, feed, "100", "200")  # avg 2/kg
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "300", "USD")
        await _expense(authed_user.farm_id, flock, authed_user.user_id, "40", "USD")
        await _feed(client, authed_user, feed, flock, "30")  # 30 x 2 = 60

        rows = [r for r in (await _full(client, authed_user))["data"] if r["asset_id"] == flock]
        assert len(rows) == 1
        row = rows[0]
        assert Decimal(row["income_total"]) == Decimal("300")
        assert Decimal(row["direct_expense_total"]) == Decimal("40")
        assert Decimal(row["consumed_material_cost"]) == Decimal("60")
        assert Decimal(row["total_cost"]) == Decimal("100")
        assert Decimal(row["net_incl_materials"]) == Decimal("200")

    async def test_net_retains_income_minus_direct_expense_only(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        await _buy_material(client, authed_user, feed, "100", "200")
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "300", "USD")
        await _expense(authed_user.farm_id, flock, authed_user.user_id, "40", "USD")
        await _feed(client, authed_user, feed, flock, "30")

        row = (await _full(client, authed_user))["data"][0]
        # net excludes feed for backward compatibility
        assert Decimal(row["net"]) == Decimal("260")

    async def test_consumed_material_cost_matches_cost_per_unit(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        await _buy_material(client, authed_user, feed, "100", "200")
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )
        await _feed(client, authed_user, feed, flock, "30")

        full_row = (await _full(client, authed_user))["data"][0]
        r3 = await client.get(
            f"{reports(authed_user.farm_id)}/cost-per-unit",
            headers=authed_user.headers,
            params={"unit": "unit"},
        )
        r3_row = r3.json()["data"][0]
        assert full_row["consumed_material_cost"] == r3_row["consumed_material_cost"]

    async def test_income_in_two_currencies_yields_a_row_each(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await _asset(authed_user.farm_id, name="Vacas")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "500", "USD")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "1000", "ARS")

        rows = {r["currency"]: r for r in (await _full(client, authed_user))["data"]}
        assert set(rows) == {"USD", "ARS"}
        assert Decimal(rows["USD"]["income_total"]) == Decimal("500")
        assert Decimal(rows["ARS"]["income_total"]) == Decimal("1000")

    async def test_feed_bought_in_non_default_currency_costs_in_that_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        await _buy_material(client, authed_user, feed, "100", "300", currency="UYU")  # 3/kg
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _feed(client, authed_user, feed, flock, "20")  # 20 x 3 = 60 UYU

        rows = [r for r in (await _full(client, authed_user))["data"] if r["asset_id"] == flock]
        assert len(rows) == 1
        assert rows[0]["currency"] == "UYU"
        assert Decimal(rows[0]["consumed_material_cost"]) == Decimal("60")
        assert Decimal(rows[0]["net_incl_materials"]) == Decimal("-60")
        assert rows[0]["has_unvalued_consumption"] is False

    async def test_mixed_currency_feed_splits_cost_proportionally_per_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        # pool: 60 kg @ 2 USD/kg + 40 kg @ 5 UYU/kg -> 100 kg total
        await _buy_material(client, authed_user, feed, "60", "120", currency="USD")
        await _buy_material(client, authed_user, feed, "40", "200", currency="UYU")
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _feed(client, authed_user, feed, flock, "50")  # 50/100 of the pool

        rows = {
            r["currency"]: r
            for r in (await _full(client, authed_user))["data"]
            if r["asset_id"] == flock
        }
        assert set(rows) == {"USD", "UYU"}
        # USD share: 50 * 120/100 = 60 ; UYU share: 50 * 200/100 = 100
        assert Decimal(rows["USD"]["consumed_material_cost"]) == Decimal("60")
        assert Decimal(rows["UYU"]["consumed_material_cost"]) == Decimal("100")

    async def test_pure_unvalued_feed_asset_appears_once_with_null_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        seed = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{feed}/events",
            headers=authed_user.headers,
            json={
                "type": "inventory",
                "occurred_at": "2026-04-01T10:00:00Z",
                "adjustment": "increment",
                "quantity": "50",
                "unit": "kg",
            },
        )
        assert seed.status_code == 201, seed.text
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _feed(client, authed_user, feed, flock, "10")

        rows = [r for r in (await _full(client, authed_user))["data"] if r["asset_id"] == flock]
        assert len(rows) == 1
        assert rows[0]["currency"] is None
        assert rows[0]["has_unvalued_consumption"] is True
        assert Decimal(rows[0]["consumed_material_cost"]) == Decimal("0")

    async def test_unvalued_feed_flagged_and_costed_zero(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        # stock arrives via a manual inventory event — no purchase, no cost basis
        seed = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{feed}/events",
            headers=authed_user.headers,
            json={
                "type": "inventory",
                "occurred_at": "2026-04-01T10:00:00Z",
                "adjustment": "increment",
                "quantity": "50",
                "unit": "kg",
            },
        )
        assert seed.status_code == 201, seed.text
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "100", "USD")
        await _feed(client, authed_user, feed, flock, "10")

        row = next(r for r in (await _full(client, authed_user))["data"] if r["asset_id"] == flock)
        assert row["has_unvalued_consumption"] is True
        assert Decimal(row["consumed_material_cost"]) == Decimal("0")

    async def test_feed_only_asset_has_negative_net_incl_materials(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        await _buy_material(client, authed_user, feed, "100", "200")
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _feed(client, authed_user, feed, flock, "30")  # 60, no income

        row = next(r for r in (await _full(client, authed_user))["data"] if r["asset_id"] == flock)
        assert Decimal(row["income_total"]) == Decimal("0")
        assert Decimal(row["consumed_material_cost"]) == Decimal("60")
        assert Decimal(row["net_incl_materials"]) == Decimal("-60")

    async def test_material_asset_excluded_so_feed_is_not_double_counted(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _material(authed_user.farm_id)
        await _buy_material(client, authed_user, feed, "100", "200")  # books 200 expense on feed
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "300", "USD")
        await _feed(client, authed_user, feed, flock, "30")  # 60 consumed

        body = await _full(client, authed_user)
        # the material asset (and its purchase expense) never appears as a row
        assert feed not in [r["asset_id"] for r in body["data"]]
        # totals count the feed once (as consumed cost), not also as a 200 purchase
        assert Decimal(body["totals"][0]["direct_expense_total"]) == Decimal("0")
        assert Decimal(body["totals"][0]["consumed_material_cost"]) == Decimal("60")
        assert Decimal(body["totals"][0]["net_incl_materials"]) == Decimal("240")

    async def test_income_only_asset_net_equals_net_incl_materials(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _income(authed_user.farm_id, flock, authed_user.user_id, "300", "USD")

        row = (await _full(client, authed_user))["data"][0]
        assert Decimal(row["consumed_material_cost"]) == Decimal("0")
        assert Decimal(row["net_incl_materials"]) == Decimal(row["net"])

    async def test_totals_sum_over_default_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        a1 = await _asset(authed_user.farm_id, name="A1")
        a2 = await _asset(authed_user.farm_id, name="A2")
        await _income(authed_user.farm_id, a1, authed_user.user_id, "100", "USD")
        await _income(authed_user.farm_id, a2, authed_user.user_id, "200", "USD")
        await _expense(authed_user.farm_id, a1, authed_user.user_id, "30", "USD")

        totals = (await _full(client, authed_user))["totals"]
        assert len(totals) == 1
        assert totals[0]["currency"] == "USD"
        assert Decimal(totals[0]["income_total"]) == Decimal("300")
        assert Decimal(totals[0]["net_incl_materials"]) == Decimal("270")

    async def test_asset_id_scopes_to_one_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        a1 = await _asset(authed_user.farm_id, name="A1")
        a2 = await _asset(authed_user.farm_id, name="A2")
        await _income(authed_user.farm_id, a1, authed_user.user_id, "100", "USD")
        await _income(authed_user.farm_id, a2, authed_user.user_id, "200", "USD")

        rows = (await _full(client, authed_user, asset_id=str(a1)))["data"]
        assert [r["asset_id"] for r in rows] == [a1]

    async def test_non_member_forbidden(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        from tests.factories import FarmFactory

        other_farm = await FarmFactory.create_async()
        resp = await client.get(
            f"{reports(int(other_farm.id))}/profitability-full", headers=authed_user.headers
        )
        assert resp.status_code == 403
