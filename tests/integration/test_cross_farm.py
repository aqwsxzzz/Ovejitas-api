"""Cross-farm reference tests.

URL-level scoping ("farm B user hits /farms/A/...") is covered by each feature's
existing TestFarmScope. This file covers the subtler case: an authenticated
user in their own farm posting/patching a body that references an entity from
a different farm. Service-layer guards must catch these.
"""

from collections.abc import Awaitable, Callable

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_AGG = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
ANIMAL_IND = {"name": "Vacas", "kind": "animal", "mode": "individual"}
OCCURRED = "2026-04-10T10:00:00Z"


def assets_url(fid: int) -> str:
    return f"/api/v1/farms/{fid}/assets"


def events_url(fid: int, aid: int) -> str:
    return f"{assets_url(fid)}/{aid}/events"


def event_url(fid: int, aid: int, eid: int) -> str:
    return f"{events_url(fid, aid)}/{eid}"


def individuals_url(fid: int, aid: int) -> str:
    return f"{assets_url(fid)}/{aid}/individuals"


def individual_url(fid: int, aid: int, iid: int) -> str:
    return f"{individuals_url(fid, aid)}/{iid}"


def categories_url(fid: int) -> str:
    return f"/api/v1/farms/{fid}/event-categories"


async def _asset(client: AsyncClient, u: AuthedUser, payload: dict) -> int:
    r = await client.post(assets_url(u.farm_id), headers=u.headers, json=payload)
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


async def _individual(client: AsyncClient, u: AuthedUser, aid: int, name: str = "X") -> int:
    r = await client.post(
        individuals_url(u.farm_id, aid),
        headers=u.headers,
        json={"name": name, "tag": f"{name}-{aid}"},
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


async def _category(client: AsyncClient, u: AuthedUser, type_: str, name: str) -> int:
    r = await client.post(
        categories_url(u.farm_id), headers=u.headers, json={"type": type_, "name": name}
    )
    assert r.status_code == 201, r.text
    return int(r.json()["id"])


class TestEventBodyReferences:
    async def test_category_from_another_farm_rejected(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("a-xf-cat@example.com")
        bob = await register_user("b-xf-cat@example.com")
        alice_asset = await _asset(client, alice, ANIMAL_AGG)
        bob_cat = await _category(client, bob, "expense", "Feed")

        resp = await client.post(
            events_url(alice.farm_id, alice_asset),
            headers=alice.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "10",
                "category_id": bob_cat,
            },
        )
        assert resp.status_code == 422
        assert "categor" in resp.json()["detail"].lower()

    async def test_patch_category_to_wrong_type_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user, ANIMAL_AGG)
        income_cat = await _category(client, authed_user, "income", "Sales")
        created = await client.post(
            events_url(authed_user.farm_id, asset_id),
            headers=authed_user.headers,
            json={
                "type": "expense",
                "occurred_at": OCCURRED,
                "amount": "10",
            },
        )
        event_id = created.json()["id"]

        resp = await client.patch(
            event_url(authed_user.farm_id, asset_id, event_id),
            headers=authed_user.headers,
            json={"category_id": income_cat},
        )
        assert resp.status_code == 422

    async def test_patch_individual_from_other_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_a = await _asset(client, authed_user, ANIMAL_IND)
        asset_b = await _asset(client, authed_user, ANIMAL_IND)
        ind_in_b = await _individual(client, authed_user, asset_b, name="in-b")
        created = await client.post(
            events_url(authed_user.farm_id, asset_a),
            headers=authed_user.headers,
            json={"type": "observation", "occurred_at": OCCURRED},
        )
        event_id = created.json()["id"]

        resp = await client.patch(
            event_url(authed_user.farm_id, asset_a, event_id),
            headers=authed_user.headers,
            json={"individual_id": ind_in_b},
        )
        assert resp.status_code == 422


class TestIndividualParentOnUpdate:
    async def test_patch_mother_from_another_farm_rejected(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("a-xf-parent@example.com")
        bob = await register_user("b-xf-parent@example.com")
        alice_asset = await _asset(client, alice, ANIMAL_IND)
        alice_calf = await _individual(client, alice, alice_asset, name="calf")
        bob_asset = await _asset(client, bob, ANIMAL_IND)
        bob_cow = await _individual(client, bob, bob_asset, name="cow-b")

        resp = await client.patch(
            individual_url(alice.farm_id, alice_asset, alice_calf),
            headers=alice.headers,
            json={"mother_id": bob_cow},
        )
        assert resp.status_code == 422
        assert "mother" in resp.json()["detail"].lower()


class TestSelfParent:
    async def test_patch_mother_to_self_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user, ANIMAL_IND)
        me = await _individual(client, authed_user, asset_id, name="lonely")

        resp = await client.patch(
            individual_url(authed_user.farm_id, asset_id, me),
            headers=authed_user.headers,
            json={"mother_id": me},
        )
        assert resp.status_code == 422
        assert "own parent" in resp.json()["detail"].lower()

    async def test_patch_mother_equal_father_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user, ANIMAL_IND)
        calf = await _individual(client, authed_user, asset_id, name="calf")
        parent = await _individual(client, authed_user, asset_id, name="only-parent")

        resp = await client.patch(
            individual_url(authed_user.farm_id, asset_id, calf),
            headers=authed_user.headers,
            json={"mother_id": parent, "father_id": parent},
        )
        assert resp.status_code == 422
        assert "same" in resp.json()["detail"].lower()


class TestIdempotency:
    async def test_same_key_across_assets_same_farm_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_a = await _asset(client, authed_user, ANIMAL_AGG)
        asset_b = await _asset(client, authed_user, ANIMAL_AGG)
        payload = {
            "type": "expense",
            "occurred_at": OCCURRED,
            "amount": "10",
            "idempotency_key": "shared-key",
        }

        first = await client.post(
            events_url(authed_user.farm_id, asset_a), headers=authed_user.headers, json=payload
        )
        assert first.status_code == 201
        second = await client.post(
            events_url(authed_user.farm_id, asset_b), headers=authed_user.headers, json=payload
        )
        assert second.status_code == 409
