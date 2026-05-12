"""Sorting, search, and pagination-boundary tests for list endpoints."""

from datetime import UTC, datetime

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetMode
from ovejitas.features.event.types import EventType
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventCategoryFactory, EventFactory


def assets_url(fid: int) -> str:
    return f"/api/v1/farms/{fid}/assets"


def events_url(fid: int, aid: int) -> str:
    return f"{assets_url(fid)}/{aid}/events"


def categories_url(fid: int) -> str:
    return f"/api/v1/farms/{fid}/event-categories"


class TestEventSearch:
    async def test_q_matches_notes(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset = await AssetFactory.create_async(farm_id=authed_user.farm_id)
        await EventFactory.create_async(
            farm_id=authed_user.farm_id,
            asset_id=asset.id,
            created_by=authed_user.user_id,
            notes="sold 20 birds",
            occurred_at=datetime(2026, 4, 1, tzinfo=UTC),
        )
        await EventFactory.create_async(
            farm_id=authed_user.farm_id,
            asset_id=asset.id,
            created_by=authed_user.user_id,
            notes="vaccinated flock",
            occurred_at=datetime(2026, 4, 2, tzinfo=UTC),
        )

        resp = await client.get(
            events_url(authed_user.farm_id, asset.id),
            headers=authed_user.headers,
            params={"q": "vaccinated"},
        )
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["notes"] == "vaccinated flock"


class TestEventSort:
    async def test_sort_by_type_asc(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset = await AssetFactory.create_async(farm_id=authed_user.farm_id)
        base = datetime(2026, 4, 1, tzinfo=UTC)
        await EventFactory.create_async(
            farm_id=authed_user.farm_id,
            asset_id=asset.id,
            created_by=authed_user.user_id,
            type=EventType.OBSERVATION,
            quantity=None,
            unit=None,
            occurred_at=base,
        )
        await EventFactory.create_async(
            farm_id=authed_user.farm_id,
            asset_id=asset.id,
            created_by=authed_user.user_id,
            type=EventType.EXPENSE,
            quantity=None,
            unit=None,
            amount="1",
            currency="USD",
            occurred_at=base,
        )

        resp = await client.get(
            events_url(authed_user.farm_id, asset.id),
            headers=authed_user.headers,
            params={"sort": "type"},
        )
        types = [r["type"] for r in resp.json()["data"]]
        assert types == ["expense", "observation"]


class TestCategorySort:
    async def test_sort_by_name_desc(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        for name in ("alpha", "bravo", "charlie"):
            await EventCategoryFactory.create_async(
                farm_id=authed_user.farm_id, type=EventType.EXPENSE, name=name
            )

        resp = await client.get(
            categories_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"sort": "-name"},
        )
        names = [r["name"] for r in resp.json()["data"]]
        assert names == ["charlie", "bravo", "alpha"]


class TestPaginationBoundaries:
    async def test_page_size_over_limit_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"page_size": 101},
        )
        assert resp.status_code == 422

    async def test_second_page_and_has_next_false(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        for i in range(3):
            await AssetFactory.create_async(
                farm_id=authed_user.farm_id,
                name=f"asset-{i}",
                mode=AssetMode.AGGREGATED,
            )

        resp = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"page": 2, "page_size": 2},
        )
        body = resp.json()
        assert body["meta"]["page"] == 2
        assert body["meta"]["total"] == 3
        assert body["meta"]["has_next"] is False
        assert len(body["data"]) == 1

    async def test_full_page_has_next_true(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        for i in range(3):
            await AssetFactory.create_async(
                farm_id=authed_user.farm_id,
                name=f"a-{i}",
            )

        resp = await client.get(
            assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"page": 1, "page_size": 2},
        )
        body = resp.json()
        assert body["meta"]["has_next"] is True
