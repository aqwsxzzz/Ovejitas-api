from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory, IndividualFactory, currency_id_for


def reports(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports"


async def _asset(farm_id: int, **kw: object) -> int:
    asset = await AssetFactory.create_async(farm_id=farm_id, **kw)
    return int(asset.id)


async def _event(farm_id: int, asset_id: int, user_id: int, **kw: object) -> None:
    when = kw.pop("when", datetime(2026, 4, 10, tzinfo=UTC))
    await EventFactory.create_async(
        farm_id=farm_id,
        asset_id=asset_id,
        created_by=user_id,
        occurred_at=when,
        **kw,
    )


class TestProfitability:
    async def test_net_per_asset(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("300"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("100"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability", headers=authed_user.headers
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        assert len(data) == 1
        row = data[0]
        assert row["asset_id"] == asset_id
        assert Decimal(row["income_total"]) == Decimal("300")
        assert Decimal(row["expense_total"]) == Decimal("100")
        assert Decimal(row["net"]) == Decimal("200")
        assert row["currency"] == "USD"

    async def test_includes_income_on_the_upper_bound_day(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # RED: reproduces "el resumen de balance no anda en el mes actual".
        # In an in-progress ("running") month the user filters up to *today*.
        # An income logged earlier today must still be counted, but the report
        # applies an inclusive `occurred_at <= date_to`, and "today" arrives as
        # midnight (00:00) — so any event later that same day is silently
        # dropped. Past months look fine only because nothing lands exactly on
        # their final midnight.
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("300"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
            when=datetime(2026, 6, 14, 9, 0, tzinfo=UTC),  # today, mid-morning
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability",
            headers=authed_user.headers,
            params={
                "date_from": "2026-06-01T00:00:00Z",
                "date_to": "2026-06-14T00:00:00Z",  # "up to today" → midnight
            },
        )

        assert resp.status_code == 200, resp.text
        rows = resp.json()["data"]
        assert len(rows) == 1, "income logged today dropped when date_to is today at 00:00"
        assert Decimal(rows[0]["income_total"]) == Decimal("300")

    async def test_totals_grouped_by_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        a1 = await _asset(authed_user.farm_id, name="A1")
        a2 = await _asset(authed_user.farm_id, name="A2")
        for asset_id in (a1, a2):
            await _event(
                authed_user.farm_id,
                asset_id,
                authed_user.user_id,
                type=EventType.INCOME,
                amount=Decimal("100"),
                currency_id=await currency_id_for(authed_user.farm_id, "USD"),
                quantity=None,
                unit=None,
            )
            await _event(
                authed_user.farm_id,
                asset_id,
                authed_user.user_id,
                type=EventType.EXPENSE,
                amount=Decimal("40"),
                currency_id=await currency_id_for(authed_user.farm_id, "USD"),
                quantity=None,
                unit=None,
            )
        await _event(
            authed_user.farm_id,
            a1,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("500"),
            currency_id=await currency_id_for(authed_user.farm_id, "ARS"),
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability", headers=authed_user.headers
        )
        totals = {t["currency"]: t for t in resp.json()["totals"]}
        assert Decimal(totals["USD"]["income_total"]) == Decimal("200")
        assert Decimal(totals["USD"]["expense_total"]) == Decimal("80")
        assert Decimal(totals["USD"]["net"]) == Decimal("120")
        assert Decimal(totals["ARS"]["income_total"]) == Decimal("500")
        assert Decimal(totals["ARS"]["net"]) == Decimal("500")

    async def test_currencies_not_mixed(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Vacas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("500"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("1000"),
            currency_id=await currency_id_for(authed_user.farm_id, "ARS"),
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability", headers=authed_user.headers
        )
        rows = {r["currency"]: r for r in resp.json()["data"]}
        assert Decimal(rows["USD"]["income_total"]) == Decimal("500")
        assert Decimal(rows["ARS"]["income_total"]) == Decimal("1000")


async def _buy_material(
    client: AsyncClient,
    authed: AuthedUser,
    material_id: int,
    quantity: str,
    amount: str,
    occurred_at: str = "2026-04-01T10:00:00Z",
    currency: str | None = None,
) -> None:
    body: dict[str, Any] = {
        "material_asset_id": material_id,
        "occurred_at": occurred_at,
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
    client: AsyncClient,
    authed: AuthedUser,
    material_id: int,
    consumer_id: int,
    quantity: str,
    occurred_at: str = "2026-04-05T10:00:00Z",
) -> None:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/material-consumptions",
        headers=authed.headers,
        json={
            "material_asset_id": material_id,
            "consumer_asset_id": consumer_id,
            "occurred_at": occurred_at,
            "quantity": quantity,
            "unit": "kg",
            "reason": "feeding",
        },
    )
    assert resp.status_code in (200, 201), resp.text


async def _cost_rows(
    client: AsyncClient, authed: AuthedUser, **params: str
) -> list[dict[str, Any]]:
    resp = await client.get(
        f"{reports(authed.farm_id)}/cost-per-unit",
        headers=authed.headers,
        params={"unit": "unit", **params},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


class TestCostPerUnit:
    async def test_cost_combines_direct_expense_and_valued_feed(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _asset(
            authed_user.farm_id, name="Feed", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED
        )
        await _buy_material(client, authed_user, feed, "100", "200")  # avg cost 2/kg
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("40"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )
        await _feed(client, authed_user, feed, flock, "30")  # 30 kg x 2 = 60

        rows = await _cost_rows(client, authed_user)
        assert len(rows) == 1
        row = rows[0]
        assert Decimal(row["production_quantity"]) == Decimal("50")
        assert Decimal(row["direct_expense_total"]) == Decimal("40")
        assert Decimal(row["consumed_material_cost"]) == Decimal("60")
        assert Decimal(row["total_cost"]) == Decimal("100")
        assert Decimal(row["cost_per_unit"]) == Decimal("2")
        assert row["has_unvalued_consumption"] is False

    async def test_feed_in_non_default_currency_costs_in_that_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _asset(
            authed_user.farm_id, name="Feed", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED
        )
        await _buy_material(client, authed_user, feed, "100", "300", currency="UYU")  # 3/kg
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )
        await _feed(client, authed_user, feed, flock, "20")  # 20 x 3 = 60 UYU

        rows = await _cost_rows(client, authed_user)
        assert len(rows) == 1
        assert rows[0]["currency"] == "UYU"
        assert Decimal(rows[0]["consumed_material_cost"]) == Decimal("60")
        assert Decimal(rows[0]["cost_per_unit"]) == Decimal("1.20")

    async def test_mixed_currency_feed_yields_a_cost_per_unit_row_each(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _asset(
            authed_user.farm_id, name="Feed", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED
        )
        await _buy_material(client, authed_user, feed, "60", "120", currency="USD")  # 2/kg
        await _buy_material(client, authed_user, feed, "40", "200", currency="UYU")  # 5/kg
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )
        await _feed(client, authed_user, feed, flock, "50")  # 50/100 of a 100 kg pool

        rows = {r["currency"]: r for r in await _cost_rows(client, authed_user)}
        assert set(rows) == {"USD", "UYU"}
        # USD: 50 * 120/100 = 60 over 50 units = 1.20 ; UYU: 50 * 200/100 = 100 = 2.00
        assert Decimal(rows["USD"]["cost_per_unit"]) == Decimal("1.20")
        assert Decimal(rows["UYU"]["cost_per_unit"]) == Decimal("2.00")

    async def test_average_cost_uses_purchases_before_date_from(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _asset(
            authed_user.farm_id, name="Feed", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED
        )
        await _buy_material(client, authed_user, feed, "100", "200", "2026-01-01T10:00:00Z")
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

        rows = await _cost_rows(client, authed_user, date_from="2026-03-01T00:00:00Z")
        # the Jan purchase still values the feed even though it precedes date_from
        assert Decimal(rows[0]["consumed_material_cost"]) == Decimal("60")

    async def test_feed_with_no_purchase_history_flags_unvalued(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        feed = await _asset(
            authed_user.farm_id, name="Feed", kind=AssetKind.MATERIAL, mode=AssetMode.AGGREGATED
        )
        # stock arrives via a manual inventory event — no purchase, no cost
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
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )
        await _feed(client, authed_user, feed, flock, "10")

        rows = await _cost_rows(client, authed_user)
        assert rows[0]["has_unvalued_consumption"] is True
        assert Decimal(rows[0]["consumed_material_cost"]) == Decimal("0")

    async def test_cost_without_production_in_window_yields_null(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
            when=datetime(2026, 1, 1, tzinfo=UTC),
        )
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("40"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )

        rows = await _cost_rows(client, authed_user, date_from="2026-03-01T00:00:00Z")
        assert Decimal(rows[0]["production_quantity"]) == Decimal("0")
        assert Decimal(rows[0]["direct_expense_total"]) == Decimal("40")
        assert rows[0]["cost_per_unit"] is None

    async def test_crop_producer_reports_like_a_flock(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        crop = await _asset(
            authed_user.farm_id, name="Tomateras", kind=AssetKind.CROP, mode=AssetMode.AGGREGATED
        )
        await _event(
            authed_user.farm_id,
            crop,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("100"),
            unit="unit",
        )
        await _event(
            authed_user.farm_id,
            crop,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("50"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )

        rows = await _cost_rows(client, authed_user)
        assert Decimal(rows[0]["cost_per_unit"]) == Decimal("0.5")

    async def test_cost_per_unit_rounded_to_cents(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("3"),
            unit="unit",
        )
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("100"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )

        rows = await _cost_rows(client, authed_user)
        # 100 / 3 = 33.333... — quantized to cents, not a 28-digit decimal
        assert rows[0]["cost_per_unit"] == "33.33"

    async def test_missing_unit_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            f"{reports(authed_user.farm_id)}/cost-per-unit", headers=authed_user.headers
        )
        assert resp.status_code == 422


class TestTimeline:
    async def test_returns_events_reverse_chrono(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Vacas", mode=AssetMode.INDIVIDUAL)
        individual = await IndividualFactory.create_async(
            farm_id=authed_user.farm_id, asset_id=asset_id, name="Vaca A"
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            individual_id=individual.id,
            when=datetime(2026, 4, 1, tzinfo=UTC),
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            individual_id=individual.id,
            when=datetime(2026, 4, 3, tzinfo=UTC),
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/individuals/{individual.id}/timeline",
            headers=authed_user.headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 2
        assert body["data"][0]["occurred_at"].startswith("2026-04-03")
        assert body["data"][1]["occurred_at"].startswith("2026-04-01")

    async def test_unknown_individual_404(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            f"{reports(authed_user.farm_id)}/individuals/999999/timeline",
            headers=authed_user.headers,
        )
        assert resp.status_code == 404


class TestPdfDownload:
    async def test_profitability_pdf(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("300"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )
        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability/pdf", headers=authed_user.headers
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"
        assert "rentabilidad.pdf" in resp.headers["content-disposition"]

    async def test_cost_per_unit_pdf(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        flock = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )
        await _event(
            authed_user.farm_id,
            flock,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("100"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
        )
        resp = await client.get(
            f"{reports(authed_user.farm_id)}/cost-per-unit/pdf",
            headers=authed_user.headers,
            params={"unit": "unit"},
        )
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"
        assert "costo-por-unidad.pdf" in resp.headers["content-disposition"]

    async def test_pdf_requires_membership(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice-pdf@example.com")
        bob = await register_user("bob-pdf@example.com")
        resp = await client.get(f"{reports(alice.farm_id)}/profitability/pdf", headers=bob.headers)
        assert resp.status_code == 403


class TestFarmScope:
    async def test_non_member_forbidden(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice-reports@example.com")
        bob = await register_user("bob-reports@example.com")

        resp = await client.get(f"{reports(alice.farm_id)}/profitability", headers=bob.headers)
        assert resp.status_code == 403

    async def test_unauthenticated_401(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        resp = await client.get(f"{reports(authed_user.farm_id)}/profitability")
        assert resp.status_code == 401
