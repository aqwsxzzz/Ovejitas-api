from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Cattle", "kind": "animal", "mode": "individual"}
EQUIPMENT_INDIVIDUAL = {"name": "Tractors", "kind": "equipment", "mode": "individual"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def individuals_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/individuals"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


async def _create_asset(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_mother(client: AsyncClient, authed: AuthedUser, asset_id: int, tag: str) -> int:
    resp = await client.post(
        individuals_url(authed.farm_id, asset_id), headers=authed.headers, json={"tag": tag}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _events(
    client: AsyncClient, authed: AuthedUser, asset_id: int, individual_id: int, event_type: str
) -> list[dict[str, object]]:
    resp = await client.get(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        params={"individual_id": individual_id, "type": event_type},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def _births_url(farm_id: int, asset_id: int, mother_id: int) -> str:
    return f"{individuals_url(farm_id, asset_id)}/{mother_id}/births"


class TestCreateBirth:
    async def test_birth_emits_reproductive_event_and_offspring(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-001")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"offspring": [{"tag": "C-1"}, {"tag": "C-2"}, {"tag": "C-3"}]},
        )

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert len(body["offspring"]) == 3
        reproductive = await _events(client, authed_user, asset_id, mother_id, "reproductive")
        assert len(reproductive) == 1
        assert reproductive[0]["id"] == body["reproductive_event_id"]
        assert reproductive[0]["payload"]["source"] == "birth"

    async def test_offspring_link_to_birth_event_and_mother(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-002")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"offspring": [{"tag": "C-1"}, {"tag": "C-2"}]},
        )

        body = resp.json()
        event_id = body["reproductive_event_id"]
        for child in body["offspring"]:
            assert child["birth_event_id"] == event_id
            assert child["mother_id"] == mother_id
            assert child["status"] == "active"

    async def test_offspring_get_born_acquisition_events(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-003")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"offspring": [{"tag": "C-1"}]},
        )

        child_id = resp.json()["offspring"][0]["id"]
        acquisitions = await _events(client, authed_user, asset_id, child_id, "acquisition")
        assert len(acquisitions) == 1
        assert acquisitions[0]["payload"]["method"] == "born"

    async def test_father_id_set_on_offspring(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-004")
        father_id = await _create_mother(client, authed_user, asset_id, "F-004")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"father_id": father_id, "offspring": [{"tag": "C-1"}, {"tag": "C-2"}]},
        )

        assert resp.status_code == 201, resp.text
        for child in resp.json()["offspring"]:
            assert child["father_id"] == father_id


class TestBirthRejections:
    async def test_birth_with_empty_offspring_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-005")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"offspring": []},
        )

        assert resp.status_code == 422

    async def test_birth_on_deceased_mother_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-006")
        patched = await client.patch(
            f"{individuals_url(authed_user.farm_id, asset_id)}/{mother_id}",
            headers=authed_user.headers,
            json={"status": "deceased"},
        )
        assert patched.status_code == 200, patched.text

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"offspring": [{"tag": "C-1"}]},
        )

        assert resp.status_code == 422

    async def test_birth_on_non_animal_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, EQUIPMENT_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-007")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"offspring": [{"tag": "C-1"}]},
        )

        assert resp.status_code == 422

    async def test_birth_with_invalid_father_writes_nothing(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)
        mother_id = await _create_mother(client, authed_user, asset_id, "M-008")

        resp = await client.post(
            _births_url(authed_user.farm_id, asset_id, mother_id),
            headers=authed_user.headers,
            json={"father_id": 999999, "offspring": [{"tag": "C-1"}]},
        )

        assert resp.status_code == 422
        assert await _events(client, authed_user, asset_id, mother_id, "reproductive") == []
