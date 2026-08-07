"""The sire and service date on a pregnancy check.

Who bred her and when she was served are recorded on the check itself, mirrored
onto the paired reproductive event, and filterable so a farm can ask which
pregnancies belong to one ram.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _pregnancies_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/pregnancies"


def _upcoming_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/upcoming-births"


async def _flock(client: AsyncClient, authed: AuthedUser, **overrides: object) -> int:
    payload: dict = {"name": "Ovejas", "kind": "animal", "mode": "individual"}
    payload.update(overrides)
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _individual(client: AsyncClient, authed: AuthedUser, asset_id: int, tag: str) -> int:
    resp = await client.post(
        f"{_assets_url(authed.farm_id)}/{asset_id}/individuals",
        headers=authed.headers,
        json={"tag": tag},
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _check(
    client: AsyncClient, authed: AuthedUser, individual_id: int, **overrides: object
) -> object:
    payload: dict = {
        "individual_id": individual_id,
        "occurred_at": "2026-06-10T10:00:00Z",
        "is_pregnant": True,
    }
    payload.update(overrides)
    return await client.post(_pregnancies_url(authed.farm_id), headers=authed.headers, json=payload)


class TestSireValidation:
    async def test_sire_is_persisted(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _flock(client, authed_user)
        ewe = await _individual(client, authed_user, asset_id, "E-001")
        ram = await _individual(client, authed_user, asset_id, "R-001")

        resp = await _check(client, authed_user, ewe, sire_individual_id=ram)

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["sire_individual_id"] == ram  # type: ignore[attr-defined]

    async def test_sire_equal_to_the_pregnant_individual_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user)
        ewe = await _individual(client, authed_user, asset_id, "E-001")

        resp = await _check(client, authed_user, ewe, sire_individual_id=ewe)

        assert resp.status_code == 422, resp.text  # type: ignore[attr-defined]

    async def test_sire_from_another_farm_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser, register_user: object
    ) -> None:
        asset_id = await _flock(client, authed_user)
        ewe = await _individual(client, authed_user, asset_id, "E-001")
        other = await register_user("other@example.com")  # type: ignore[operator]
        other_asset = await _flock(client, other)
        foreign_ram = await _individual(client, other, other_asset, "R-999")

        resp = await _check(client, authed_user, ewe, sire_individual_id=foreign_ram)

        assert resp.status_code == 422, resp.text  # type: ignore[attr-defined]


class TestSireFilter:
    async def test_list_filters_by_sire(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id = await _flock(client, authed_user)
        ram = await _individual(client, authed_user, asset_id, "R-001")
        first = await _individual(client, authed_user, asset_id, "E-001")
        second = await _individual(client, authed_user, asset_id, "E-002")
        await _check(client, authed_user, first, sire_individual_id=ram)
        await _check(client, authed_user, second)

        resp = await client.get(
            _pregnancies_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"sire_individual_id": ram},
        )

        assert resp.status_code == 200, resp.text
        rows = resp.json()["data"]
        assert [row["individual_id"] for row in rows] == [first]


class TestDerivedRowReachesTheReport:
    async def test_derived_due_date_appears_in_upcoming_births(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)
        ewe = await _individual(client, authed_user, asset_id, "E-001")
        await _check(client, authed_user, ewe)

        resp = await client.get(
            _upcoming_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"date_from": "2026-11-01T00:00:00Z", "date_to": "2026-11-30T00:00:00Z"},
        )

        assert resp.status_code == 200, resp.text
        assert [row["individual_id"] for row in resp.json()["data"]] == [ewe]
