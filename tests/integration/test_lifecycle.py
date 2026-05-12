"""Cascade / lifecycle tests — verify FK ondelete behavior holds."""

from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ovejitas.features.asset.models import AssetMode
from ovejitas.features.event.models import Event
from ovejitas.features.event.types import EventType
from ovejitas.features.individual.models import Individual
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, EventFactory, IndividualFactory


class TestAssetDeleteCascade:
    async def test_deleting_asset_removes_events_and_individuals(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        db_session: AsyncSession,
    ) -> None:
        asset = await AssetFactory.create_async(
            farm_id=authed_user.farm_id, mode=AssetMode.INDIVIDUAL
        )
        individual = await IndividualFactory.create_async(
            farm_id=authed_user.farm_id, asset_id=asset.id, name="Doomed"
        )
        await EventFactory.create_async(
            farm_id=authed_user.farm_id,
            asset_id=asset.id,
            individual_id=individual.id,
            created_by=authed_user.user_id,
            type=EventType.OBSERVATION,
            quantity=None,
            unit=None,
            occurred_at=datetime(2026, 4, 1, tzinfo=UTC),
        )

        resp = await client.delete(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset.id}",
            headers=authed_user.headers,
        )
        assert resp.status_code == 204

        events = (
            await db_session.execute(
                select(func.count()).select_from(Event).where(Event.asset_id == asset.id)
            )
        ).scalar_one()
        individuals = (
            await db_session.execute(
                select(func.count()).select_from(Individual).where(Individual.asset_id == asset.id)
            )
        ).scalar_one()
        assert events == 0
        assert individuals == 0
