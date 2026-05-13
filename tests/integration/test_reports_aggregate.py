"""Tests for the generic /reports/aggregate endpoint."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from ovejitas.features.event.types import EventType, InventoryAdjustment, Unit
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory


def aggregate_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/aggregate"


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


class TestType:
    async def test_type_required(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        resp = await client.get(aggregate_url(authed_user.farm_id), headers=authed_user.headers)
        assert resp.status_code == 422


class TestProductionAndObservation:
    async def test_production_sum_by_unit(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Gallinas")
        day1 = datetime(2026, 4, 1, tzinfo=UTC)
        day2 = datetime(2026, 4, 2, tzinfo=UTC)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("10"),
            unit=Unit.UNIT,
            when=day1,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("5"),
            unit=Unit.UNIT,
            when=day1,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("7"),
            unit=Unit.UNIT,
            when=day2,
        )

        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "production", "bucket": "day"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["meta"] == {
            "type": "production",
            "measure": "sum_quantity",
            "bucket": "day",
            "group_key": "unit",
        }
        by_day = {r["bucket"][:10]: Decimal(r["value"]) for r in body["data"]}
        assert by_day == {"2026-04-01": Decimal("15"), "2026-04-02": Decimal("7")}
        assert {r["group"] for r in body["data"]} == {"unit"}

    async def test_observation_dispatches_to_quantity_by_unit(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.OBSERVATION,
            quantity=Decimal("200"),
            unit=Unit.UNIT,
        )
        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "observation"},
        )
        assert resp.status_code == 200
        assert resp.json()["meta"]["group_key"] == "unit"
        assert Decimal(resp.json()["data"][0]["value"]) == Decimal("200")


class TestMortalityAndAcquisition:
    async def test_mortality_headcount(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, name="Vacas")
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.MORTALITY,
            quantity=Decimal("2"),
            unit=None,
            when=datetime(2026, 4, 1, tzinfo=UTC),
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.MORTALITY,
            quantity=Decimal("1"),
            unit=None,
            when=datetime(2026, 4, 1, tzinfo=UTC),
        )

        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "mortality"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["meta"]["group_key"] is None
        assert body["meta"]["measure"] == "sum_quantity"
        assert len(body["data"]) == 1
        assert body["data"][0]["group"] is None
        assert Decimal(body["data"][0]["value"]) == Decimal("3")

    async def test_acquisition_headcount(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.ACQUISITION,
            quantity=Decimal("5"),
            unit=None,
        )
        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "acquisition"},
        )
        assert resp.status_code == 200
        assert Decimal(resp.json()["data"][0]["value"]) == Decimal("5")


class TestExpenseAndIncome:
    async def test_expense_sum_by_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id)
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
            type=EventType.EXPENSE,
            amount=Decimal("250"),
            currency="ARS",
            quantity=None,
            unit=None,
        )

        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "expense"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["measure"] == "sum_amount"
        assert body["meta"]["group_key"] == "currency"
        by_cur = {r["group"]: Decimal(r["value"]) for r in body["data"]}
        assert by_cur == {"USD": Decimal("100"), "ARS": Decimal("250")}


class TestInventoryAggregate:
    async def _material(self, farm_id: int) -> int:
        return await _asset(farm_id, name="Maíz", kind=AssetKind.MATERIAL)

    async def test_net_flow_excludes_resets(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await self._material(authed_user.farm_id)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INVENTORY,
            adjustment=InventoryAdjustment.RESET,
            quantity=Decimal("100"),
            unit=Unit.KG,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INVENTORY,
            adjustment=InventoryAdjustment.INCREMENT,
            quantity=Decimal("50"),
            unit=Unit.KG,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INVENTORY,
            adjustment=InventoryAdjustment.DECREMENT,
            quantity=Decimal("20"),
            unit=Unit.KG,
        )

        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "inventory"},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["data"][0]["value"]) == Decimal("30")

    async def test_adjustment_filter_increment_only(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await self._material(authed_user.farm_id)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INVENTORY,
            adjustment=InventoryAdjustment.INCREMENT,
            quantity=Decimal("80"),
            unit=Unit.KG,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            type=EventType.INVENTORY,
            adjustment=InventoryAdjustment.DECREMENT,
            quantity=Decimal("30"),
            unit=Unit.KG,
        )
        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "inventory", "adjustment": "increment"},
        )
        assert resp.status_code == 200
        assert Decimal(resp.json()["data"][0]["value"]) == Decimal("80")


class TestReproductive:
    async def test_count(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id, mode=AssetMode.INDIVIDUAL)
        from tests.factories import IndividualFactory

        ind = await IndividualFactory.create_async(
            farm_id=authed_user.farm_id, asset_id=asset_id, name="Cow"
        )
        for _ in range(3):
            await _event(
                authed_user.farm_id,
                asset_id,
                authed_user.user_id,
                type=EventType.REPRODUCTIVE,
                individual_id=ind.id,
                quantity=None,
                unit=None,
            )

        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "reproductive"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["meta"]["measure"] == "count"
        assert body["meta"]["group_key"] is None
        assert Decimal(body["data"][0]["value"]) == Decimal("3")


class TestFilters:
    async def test_date_range(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _asset(authed_user.farm_id)
        in_range = datetime(2026, 4, 10, tzinfo=UTC)
        out_range = datetime(2026, 3, 1, tzinfo=UTC)
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("10"),
            unit=Unit.UNIT,
            when=in_range,
        )
        await _event(
            authed_user.farm_id,
            asset_id,
            authed_user.user_id,
            quantity=Decimal("999"),
            unit=Unit.UNIT,
            when=out_range,
        )

        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "production", "date_from": "2026-04-01T00:00:00Z"},
        )
        assert resp.status_code == 200
        total = sum(Decimal(r["value"]) for r in resp.json()["data"])
        assert total == Decimal("10")

    async def test_week_bucket_collapses(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(authed_user.farm_id)
        monday = datetime(2026, 4, 6, tzinfo=UTC)
        for offset in range(3):
            await _event(
                authed_user.farm_id,
                asset_id,
                authed_user.user_id,
                quantity=Decimal("10"),
                unit=Unit.UNIT,
                when=monday + timedelta(days=offset),
            )
        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "production", "bucket": "week"},
        )
        body = resp.json()
        assert len(body["data"]) == 1
        assert Decimal(body["data"][0]["value"]) == Decimal("30")

    async def test_asset_id_filter(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        a1 = await _asset(authed_user.farm_id, name="A1")
        a2 = await _asset(authed_user.farm_id, name="A2")
        for aid in (a1, a2):
            await _event(
                authed_user.farm_id,
                aid,
                authed_user.user_id,
                quantity=Decimal("5"),
                unit=Unit.UNIT,
            )
        resp = await client.get(
            aggregate_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"type": "production", "asset_id": a1},
        )
        rows = resp.json()["data"]
        assert len(rows) == 1
        assert Decimal(rows[0]["value"]) == Decimal("5")
