from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetMode
from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory, IndividualFactory


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
            currency="USD",
            quantity=None,
            unit=None,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("100"),
            currency="USD",
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

    async def test_currencies_not_mixed(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Vacas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("500"),
            currency="USD",
            quantity=None,
            unit=None,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("1000"),
            currency="ARS",
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability", headers=authed_user.headers
        )
        rows = {r["currency"]: r for r in resp.json()["data"]}
        assert Decimal(rows["USD"]["income_total"]) == Decimal("500")
        assert Decimal(rows["ARS"]["income_total"]) == Decimal("1000")


class TestProduction:
    async def test_bucketed_sum(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        day1 = datetime(2026, 4, 1, tzinfo=UTC)
        day2 = datetime(2026, 4, 2, tzinfo=UTC)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("10"),
            unit="unit",
            when=day1,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("5"),
            unit="unit",
            when=day1,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("7"),
            unit="unit",
            when=day2,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/production",
            headers=authed_user.headers,
            params={"bucket": "day"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["type"] == "production"
        totals = {row["bucket_start"][:10]: Decimal(row["total"]) for row in body["data"]}
        assert totals["2026-04-01"] == Decimal("15")
        assert totals["2026-04-02"] == Decimal("7")

    async def test_observation_headcount(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.OBSERVATION,
            quantity=Decimal("200"),
            unit="unit",
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.OBSERVATION,
            quantity=Decimal("-5"),
            unit="unit",
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/production",
            headers=authed_user.headers,
            params={"type": "observation", "unit": "unit"},
        )
        assert resp.status_code == 200
        total = sum(Decimal(r["total"]) for r in resp.json()["data"])
        assert total == Decimal("195")


class TestCostPerUnit:
    async def test_expense_over_production(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.EXPENSE,
            amount=Decimal("100"),
            currency="USD",
            quantity=None,
            unit=None,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.PRODUCTION,
            quantity=Decimal("50"),
            unit="unit",
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/cost-per-unit",
            headers=authed_user.headers,
            params={"unit": "unit"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["unit"] == "unit"
        assert len(body["data"]) == 1
        assert Decimal(body["data"][0]["cost_per_unit"]) == Decimal("2")

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
