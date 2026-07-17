"""Report filter / bucket / edge-case tests (companion to test_reports.py)."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetMode
from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory, IndividualFactory, currency_id_for


def reports(fid: int) -> str:
    return f"/api/v1/farms/{fid}/reports"


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


class TestProfitabilityFilters:
    async def test_date_range_excludes_out_of_range(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id)
        in_range = datetime(2026, 4, 10, tzinfo=UTC)
        out_range = datetime(2026, 3, 1, tzinfo=UTC)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("100"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
            when=in_range,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INCOME,
            amount=Decimal("999"),
            currency_id=await currency_id_for(authed_user.farm_id, "USD"),
            quantity=None,
            unit=None,
            when=out_range,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability",
            headers=authed_user.headers,
            params={"date_from": "2026-04-01T00:00:00Z"},
        )
        assert Decimal(resp.json()["data"][0]["income_total"]) == Decimal("100")

    async def test_asset_id_filter(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        a1 = await _asset(authed_user.farm_id, name="A1")
        a2 = await _asset(authed_user.farm_id, name="A2")
        for aid, amt in [(a1, "100"), (a2, "500")]:
            await _event(
                authed_user.farm_id,
                aid,
                authed_user.user_id,
                type=EventType.INCOME,
                amount=Decimal(amt),
                currency_id=await currency_id_for(authed_user.farm_id, "USD"),
                quantity=None,
                unit=None,
            )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/profitability",
            headers=authed_user.headers,
            params={"asset_id": a2},
        )
        rows = resp.json()["data"]
        assert len(rows) == 1
        assert rows[0]["asset_id"] == a2


class TestCostPerUnitEdges:
    async def test_asset_with_expense_but_no_production_omitted(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id)
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
            f"{reports(authed_user.farm_id)}/cost-per-unit",
            headers=authed_user.headers,
            params={"unit": "unit"},
        )
        assert resp.json()["data"] == []


class TestTimelineEdges:
    async def test_individual_from_other_farm_returns_404(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice-xf-timeline@example.com")
        bob = await register_user("bob-xf-timeline@example.com")
        bob_asset = await _asset(bob.farm_id, mode=AssetMode.INDIVIDUAL)
        bob_ind = await IndividualFactory.create_async(
            farm_id=bob.farm_id, asset_id=bob_asset, name="Bob's cow"
        )

        resp = await client.get(
            f"{reports(alice.farm_id)}/individuals/{bob_ind.id}/timeline",
            headers=alice.headers,
        )
        assert resp.status_code == 404

    async def test_type_filter(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, mode=AssetMode.INDIVIDUAL)
        ind = await IndividualFactory.create_async(
            farm_id=authed_user.farm_id, asset_id=asset_id, name="Cow"
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            individual_id=ind.id,
            type=EventType.PRODUCTION,
            quantity=Decimal("1"),
            unit="l",
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            individual_id=ind.id,
            type=EventType.OBSERVATION,
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/individuals/{ind.id}/timeline",
            headers=authed_user.headers,
            params={"type": "production"},
        )
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["type"] == "production"

    async def test_pagination(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, mode=AssetMode.INDIVIDUAL)
        ind = await IndividualFactory.create_async(
            farm_id=authed_user.farm_id, asset_id=asset_id, name="Cow"
        )
        for i in range(5):
            await _event(
                authed_user.farm_id,
                asset_id,
                authed_user.user_id,
                individual_id=ind.id,
                type=EventType.OBSERVATION,
                quantity=None,
                unit=None,
                when=datetime(2026, 4, 1 + i, tzinfo=UTC),
            )

        resp = await client.get(
            f"{reports(authed_user.farm_id)}/individuals/{ind.id}/timeline",
            headers=authed_user.headers,
            params={"page": 2, "page_size": 2},
        )
        body = resp.json()
        assert body["meta"]["total"] == 5
        assert body["meta"]["page"] == 2
        assert body["meta"]["has_next"] is True
        assert len(body["data"]) == 2
