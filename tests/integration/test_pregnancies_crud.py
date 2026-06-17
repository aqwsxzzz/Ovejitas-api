"""Stage 5 — pregnancy read/list/update coverage (CRUD beyond create/delete)."""

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Ovejas", "kind": "animal", "mode": "individual"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _pregnancies_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/pregnancies"


def _timeline_url(farm_id: int, individual_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/individuals/{individual_id}/timeline"


async def _individual(client: AsyncClient, authed: AuthedUser, tag: str) -> int:
    asset = await client.post(
        _assets_url(authed.farm_id), headers=authed.headers, json=ANIMAL_INDIVIDUAL
    )
    ind = await client.post(
        f"{_assets_url(authed.farm_id)}/{asset.json()['id']}/individuals",
        headers=authed.headers,
        json={"tag": tag},
    )
    return int(ind.json()["id"])


async def _create(
    client: AsyncClient, authed: AuthedUser, individual_id: int, *, is_pregnant: bool = True
) -> dict:
    payload: dict = {
        "individual_id": individual_id,
        "occurred_at": "2026-06-10T10:00:00Z",
        "is_pregnant": is_pregnant,
        "offspring_count": 2 if is_pregnant else None,
        "expected_due_at": "2026-11-10T00:00:00Z" if is_pregnant else None,
    }
    resp = await client.post(_pregnancies_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestGetPregnancy:
    async def test_get_returns_the_record(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user, "G-1")
        created = await _create(client, authed_user, individual_id)

        resp = await client.get(
            f"{_pregnancies_url(authed_user.farm_id)}/{created['id']}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == created["id"]

    async def test_get_unknown_returns_404(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(
            f"{_pregnancies_url(authed_user.farm_id)}/999999", headers=authed_user.headers
        )

        assert resp.status_code == 404

    async def test_get_from_another_farm_returns_404(
        self, client: AsyncClient, authed_user: AuthedUser, register_user: object
    ) -> None:
        other = await register_user("other@example.com")  # type: ignore[operator]
        other_individual = await _individual(client, other, "O-1")
        other_pregnancy = await _create(client, other, other_individual)

        resp = await client.get(
            f"{_pregnancies_url(authed_user.farm_id)}/{other_pregnancy['id']}",
            headers=authed_user.headers,
        )

        assert resp.status_code == 404


class TestListPregnancies:
    async def test_list_returns_paginated_envelope(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user, "L-1")
        await _create(client, authed_user, individual_id)

        resp = await client.get(_pregnancies_url(authed_user.farm_id), headers=authed_user.headers)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["meta"]["total"] == 1
        assert len(body["data"]) == 1

    async def test_filter_by_is_pregnant(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        pregnant = await _individual(client, authed_user, "L-2")
        empty = await _individual(client, authed_user, "L-3")
        await _create(client, authed_user, pregnant, is_pregnant=True)
        await _create(client, authed_user, empty, is_pregnant=False)

        resp = await client.get(
            _pregnancies_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"is_pregnant": "true"},
        )

        assert resp.status_code == 200, resp.text
        ids = {row["individual_id"] for row in resp.json()["data"]}
        assert ids == {pregnant}

    async def test_filter_by_individual_id(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        a = await _individual(client, authed_user, "L-4")
        b = await _individual(client, authed_user, "L-5")
        await _create(client, authed_user, a)
        await _create(client, authed_user, b)

        resp = await client.get(
            _pregnancies_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"individual_id": b},
        )

        assert resp.status_code == 200, resp.text
        ids = {row["individual_id"] for row in resp.json()["data"]}
        assert ids == {b}


class TestUpdatePregnancy:
    async def test_update_offspring_count_succeeds(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user, "U-1")
        created = await _create(client, authed_user, individual_id)

        resp = await client.patch(
            f"{_pregnancies_url(authed_user.farm_id)}/{created['id']}",
            headers=authed_user.headers,
            json={"offspring_count": 3},
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["offspring_count"] == 3

    async def test_update_occurred_at_reconciles_paired_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user, "U-2")
        created = await _create(client, authed_user, individual_id)

        patch = await client.patch(
            f"{_pregnancies_url(authed_user.farm_id)}/{created['id']}",
            headers=authed_user.headers,
            json={"occurred_at": "2026-06-15T10:00:00Z"},
        )
        assert patch.status_code == 200, patch.text

        timeline = await client.get(
            _timeline_url(authed_user.farm_id, individual_id), headers=authed_user.headers
        )
        repro = [r for r in timeline.json()["data"] if r["type"] == "reproductive"]
        assert len(repro) == 1
        assert repro[0]["occurred_at"].startswith("2026-06-15")
