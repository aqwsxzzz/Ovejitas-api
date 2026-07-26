"""Calendar dates the API derives or stamps are the farm's, not UTC's.

Covers the three places a bare date or wall clock is produced rather than
filtered: the timezone a new farm starts on, a newborn's birth_date, and the
"generated" stamp on a report PDF.
"""

from httpx import AsyncClient

from ovejitas.features.asset.models import AssetKind, AssetMode
from tests.conftest import AuthedUser
from tests.factories import AssetFactory, IndividualFactory

MONTEVIDEO = "America/Montevideo"
# 2026-04-10 23:30 in Montevideo — already the 11th in UTC.
LATE_LOCAL_EVENING = "2026-04-11T02:30:00Z"


class TestSignupTimezone:
    async def test_register_without_timezone_defaults_the_farm_to_utc(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "no-tz@example.com", "name": "No TZ", "password": "password123"},
        )
        assert resp.status_code == 201, resp.text

        assert await _farm_timezone(client, resp.json()["access_token"]) == "UTC"

    async def test_register_with_timezone_starts_the_farm_on_that_calendar(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "with-tz@example.com",
                "name": "With TZ",
                "password": "password123",
                "timezone": MONTEVIDEO,
            },
        )
        assert resp.status_code == 201, resp.text

        assert await _farm_timezone(client, resp.json()["access_token"]) == MONTEVIDEO

    async def test_register_with_an_unknown_timezone_is_rejected(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bad-tz@example.com",
                "name": "Bad TZ",
                "password": "password123",
                "timezone": "Mars/Olympus_Mons",
            },
        )

        assert resp.status_code == 422


async def _farm_timezone(client: AsyncClient, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    farm_id = me.json()["memberships"][0]["farm_id"]
    farm = await client.get(f"/api/v1/farms/{farm_id}", headers=headers)
    assert farm.status_code == 200, farm.text
    tz: str = farm.json()["timezone"]
    return tz


class TestBirthDateIsTheFarmsCalendarDay:
    async def _mother(self, user: AuthedUser) -> tuple[int, int]:
        asset = await AssetFactory.create_async(
            farm_id=user.farm_id, kind=AssetKind.ANIMAL, mode=AssetMode.INDIVIDUAL
        )
        mother = await IndividualFactory.create_async(
            farm_id=user.farm_id, asset_id=asset.id, name="Oveja"
        )
        return int(asset.id), int(mother.id)

    async def test_evening_birth_is_dated_to_the_local_day_not_the_utc_one(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, MONTEVIDEO)
        asset_id, mother_id = await self._mother(authed_user)

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}"
            f"/individuals/{mother_id}/births",
            headers=authed_user.headers,
            json={
                "occurred_at": LATE_LOCAL_EVENING,
                "offspring": [{"tag": "C-001", "name": "Cordero"}],
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["offspring"][0]["birth_date"] == "2026-04-10"

    async def test_an_explicit_birth_date_is_never_overridden(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        await _set_timezone(client, authed_user, MONTEVIDEO)
        asset_id, mother_id = await self._mother(authed_user)

        resp = await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}"
            f"/individuals/{mother_id}/births",
            headers=authed_user.headers,
            json={
                "occurred_at": LATE_LOCAL_EVENING,
                "offspring": [{"tag": "C-002", "name": "Cordero", "birth_date": "2026-04-01"}],
            },
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["offspring"][0]["birth_date"] == "2026-04-01"


class TestPdfIsStampedOnTheFarmsClock:
    async def test_profitability_pdf_renders(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        """The stamp itself is 'now', so this pins that the farm's zone reaches
        the renderer at all — a missing dep would 500 rather than mis-stamp."""
        await _set_timezone(client, authed_user, MONTEVIDEO)

        resp = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/reports/profitability/pdf",
            headers=authed_user.headers,
            params={"date_from": "2026-04-01", "date_to": "2026-04-10"},
        )

        assert resp.status_code == 200, resp.text
        assert resp.content.startswith(b"%PDF")


async def _set_timezone(client: AsyncClient, user: AuthedUser, name: str) -> None:
    resp = await client.patch(
        f"/api/v1/farms/{user.farm_id}", headers=user.headers, json={"timezone": name}
    )
    assert resp.status_code == 200, resp.text
