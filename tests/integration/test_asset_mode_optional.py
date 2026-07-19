"""Stage 1 — material assets may have no tracking mode.

``mode`` is only meaningful for animals (they back the individual feature).
Materials/equipment/location/crops may omit it; animals must declare one.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


async def _create(client: AsyncClient, authed: AuthedUser, payload: dict) -> object:
    return await client.post(_assets_url(authed.farm_id), headers=authed.headers, json=payload)


class TestCreateMode:
    async def test_material_without_mode_persists_null(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create(client, authed_user, {"name": "Maíz", "kind": "material"})

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["mode"] is None  # type: ignore[attr-defined]

    async def test_animal_without_mode_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create(client, authed_user, {"name": "Gallinas", "kind": "animal"})

        assert resp.status_code == 422, resp.text  # type: ignore[attr-defined]

    async def test_material_with_mode_still_accepted_for_backcompat(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create(
            client, authed_user, {"name": "Sal", "kind": "material", "mode": "aggregated"}
        )

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["mode"] == "aggregated"  # type: ignore[attr-defined]

    async def test_animal_with_mode_is_accepted(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await _create(
            client, authed_user, {"name": "Vacas", "kind": "animal", "mode": "individual"}
        )

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        assert resp.json()["mode"] == "individual"  # type: ignore[attr-defined]


class TestUpdateMode:
    async def test_clearing_an_animal_mode_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await _create(
            client, authed_user, {"name": "Vacas", "kind": "animal", "mode": "aggregated"}
        )
        asset_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_assets_url(authed_user.farm_id)}/{asset_id}",
            headers=authed_user.headers,
            json={"mode": None},
        )

        assert resp.status_code == 422, resp.text
