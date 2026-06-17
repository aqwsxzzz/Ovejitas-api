"""Stage 5 — structured pregnancy records.

A pregnancy is recorded against one individual and owns a paired REPRODUCTIVE
event on that individual's timeline. A non-pregnant check carries no projection.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Ovejas", "kind": "animal", "mode": "individual"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _pregnancies_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/pregnancies"


def _timeline_url(farm_id: int, individual_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/individuals/{individual_id}/timeline"


async def _individual(client: AsyncClient, authed: AuthedUser, tag: str = "E-001") -> int:
    asset = await client.post(
        _assets_url(authed.farm_id), headers=authed.headers, json=ANIMAL_INDIVIDUAL
    )
    assert asset.status_code == 201, asset.text
    ind = await client.post(
        f"{_assets_url(authed.farm_id)}/{asset.json()['id']}/individuals",
        headers=authed.headers,
        json={"tag": tag},
    )
    assert ind.status_code == 201, ind.text
    return int(ind.json()["id"])


async def _create_pregnancy(
    client: AsyncClient, authed: AuthedUser, individual_id: int, **overrides: object
) -> object:
    payload: dict = {
        "individual_id": individual_id,
        "occurred_at": "2026-06-10T10:00:00Z",
        "is_pregnant": True,
        "offspring_count": 2,
        "expected_due_at": "2026-11-10T00:00:00Z",
    }
    payload.update(overrides)
    return await client.post(_pregnancies_url(authed.farm_id), headers=authed.headers, json=payload)


class TestCreatePregnancy:
    async def test_pregnant_check_persists_projection(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)

        resp = await _create_pregnancy(client, authed_user, individual_id)

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]
        body = resp.json()  # type: ignore[attr-defined]
        assert body["is_pregnant"] is True
        assert body["offspring_count"] == 2
        assert body["reproductive_event_id"] is not None

    async def test_not_pregnant_with_offspring_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)

        resp = await _create_pregnancy(
            client,
            authed_user,
            individual_id,
            is_pregnant=False,
            offspring_count=1,
            expected_due_at=None,
        )

        assert resp.status_code == 422, resp.text  # type: ignore[attr-defined]

    async def test_not_pregnant_without_projection_is_accepted(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)

        resp = await _create_pregnancy(
            client,
            authed_user,
            individual_id,
            is_pregnant=False,
            offspring_count=None,
            expected_due_at=None,
        )

        assert resp.status_code == 201, resp.text  # type: ignore[attr-defined]

    async def test_individual_from_another_farm_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser, register_user: object
    ) -> None:
        other = await register_user("other@example.com")  # type: ignore[operator]
        other_individual = await _individual(client, other)

        resp = await _create_pregnancy(client, authed_user, other_individual)

        assert resp.status_code in (403, 404), resp.text  # type: ignore[attr-defined]


class TestPregnancyEventLifecycle:
    async def test_create_emits_reproductive_event_on_timeline(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)
        await _create_pregnancy(client, authed_user, individual_id)

        resp = await client.get(
            _timeline_url(authed_user.farm_id, individual_id), headers=authed_user.headers
        )

        assert resp.status_code == 200, resp.text
        types = [row["type"] for row in resp.json()["data"]]
        assert "reproductive" in types

    async def test_delete_reverses_the_reproductive_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)
        created = await _create_pregnancy(client, authed_user, individual_id)
        pregnancy_id = created.json()["id"]  # type: ignore[attr-defined]

        deleted = await client.delete(
            f"{_pregnancies_url(authed_user.farm_id)}/{pregnancy_id}",
            headers=authed_user.headers,
        )

        assert deleted.status_code == 204
        timeline = await client.get(
            _timeline_url(authed_user.farm_id, individual_id), headers=authed_user.headers
        )
        # the individual's acquisition event stays; only the reproductive one is reversed
        types = [row["type"] for row in timeline.json()["data"]]
        assert "reproductive" not in types


class TestUpdatePregnancy:
    async def test_clearing_pregnant_without_projection_is_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)
        created = await _create_pregnancy(client, authed_user, individual_id)
        pregnancy_id = created.json()["id"]  # type: ignore[attr-defined]

        resp = await client.patch(
            f"{_pregnancies_url(authed_user.farm_id)}/{pregnancy_id}",
            headers=authed_user.headers,
            json={"is_pregnant": False},
        )

        assert resp.status_code == 422, resp.text


class TestIdempotency:
    async def test_replay_returns_existing_record(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        individual_id = await _individual(client, authed_user)
        first = await _create_pregnancy(
            client, authed_user, individual_id, idempotency_key="preg-1"
        )
        second = await _create_pregnancy(
            client, authed_user, individual_id, idempotency_key="preg-1"
        )

        assert first.status_code == 201  # type: ignore[attr-defined]
        assert second.status_code == 200  # type: ignore[attr-defined]
        assert first.json()["id"] == second.json()["id"]  # type: ignore[attr-defined]
