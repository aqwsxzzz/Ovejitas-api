"""Deriving a pregnancy check's expected due date from the asset's gestation length.

A positive check that omits the due date gets one projected from the flock's
gestation length, counted from the service date when there is one. An asset
with no gestation length configured behaves exactly as it did before.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _pregnancies_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/pregnancies"


async def _flock(client: AsyncClient, authed: AuthedUser, **overrides: object) -> int:
    payload: dict = {"name": "Ovejas", "kind": "animal", "mode": "individual"}
    payload.update(overrides)
    resp = await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _individual(
    client: AsyncClient, authed: AuthedUser, asset_id: int, tag: str = "E-001"
) -> int:
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


class TestGestationOnAsset:
    async def test_gestation_days_is_stored_and_read_back(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)

        resp = await client.get(
            f"{_assets_url(authed_user.farm_id)}/{asset_id}", headers=authed_user.headers
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["gestation_days"] == 150

    async def test_gestation_days_below_range_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.post(
            _assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"name": "Ovejas", "kind": "animal", "mode": "individual", "gestation_days": 3},
        )

        assert resp.status_code == 422, resp.text

    async def test_gestation_days_on_non_animal_asset_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.post(
            _assets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json={"name": "Galpon", "kind": "location", "gestation_days": 150},
        )

        assert resp.status_code == 422, resp.text


class TestDerivedDueDate:
    async def test_omitted_due_date_is_derived_from_the_check_date(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)
        individual_id = await _individual(client, authed_user, asset_id)

        resp = await _check(client, authed_user, individual_id)

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["expected_due_at"].startswith("2026-11-07")  # type: ignore[attr-defined]

    async def test_service_date_is_preferred_over_the_check_date_as_base(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)
        individual_id = await _individual(client, authed_user, asset_id)

        resp = await _check(client, authed_user, individual_id, service_date="2026-05-01T10:00:00Z")

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["expected_due_at"].startswith("2026-09-28")  # type: ignore[attr-defined]

    async def test_explicit_due_date_is_preserved_unchanged(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)
        individual_id = await _individual(client, authed_user, asset_id)

        resp = await _check(
            client, authed_user, individual_id, expected_due_at="2026-12-25T00:00:00Z"
        )

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["expected_due_at"].startswith("2026-12-25")  # type: ignore[attr-defined]

    async def test_asset_without_gestation_derives_nothing(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user)
        individual_id = await _individual(client, authed_user, asset_id)

        resp = await _check(client, authed_user, individual_id)

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["expected_due_at"] is None  # type: ignore[attr-defined]

    async def test_negative_check_derives_nothing(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)
        individual_id = await _individual(client, authed_user, asset_id)

        resp = await _check(client, authed_user, individual_id, is_pregnant=False)

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["expected_due_at"] is None  # type: ignore[attr-defined]

    async def test_changing_gestation_afterwards_leaves_the_due_date_alone(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _flock(client, authed_user, gestation_days=150)
        individual_id = await _individual(client, authed_user, asset_id)
        created = await _check(client, authed_user, individual_id)
        pregnancy_id = created.json()["id"]  # type: ignore[attr-defined]

        await client.patch(
            f"{_assets_url(authed_user.farm_id)}/{asset_id}",
            headers=authed_user.headers,
            json={"gestation_days": 280},
        )

        resp = await client.get(
            f"{_pregnancies_url(authed_user.farm_id)}/{pregnancy_id}",
            headers=authed_user.headers,
        )
        assert resp.json()["expected_due_at"].startswith("2026-11-07")
