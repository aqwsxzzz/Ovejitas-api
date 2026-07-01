from collections.abc import Awaitable, Callable
from decimal import Decimal

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_AGGREGATED = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
CROP_AGGREGATED = {"name": "Maíz", "kind": "crop", "mode": "aggregated"}


def targets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/production-targets"


def target_url(farm_id: int, target_id: int) -> str:
    return f"{targets_url(farm_id)}/{target_id}"


def _payload(asset_id: int, category_id: int, **overrides: object) -> dict[str, object]:
    """A valid per_head_continuous target body; override fields per case."""
    body: dict[str, object] = {
        "asset_id": asset_id,
        "category_id": category_id,
        "basis": "per_head_continuous",
        "expected_rate": "0.8",
        "period": "day",
        "effective_from": "2026-01-01",
    }
    body.update(overrides)
    return body


async def _create_asset(client: AsyncClient, authed: AuthedUser, payload: dict[str, str]) -> int:
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/assets", headers=authed.headers, json=payload
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _category(
    client: AsyncClient, authed: AuthedUser, event_type: str, name: str, unit: str | None = None
) -> int:
    body: dict[str, str] = {"type": event_type, "name": name}
    if unit is not None:
        body["unit"] = unit
    resp = await client.post(
        f"/api/v1/farms/{authed.farm_id}/event-categories", headers=authed.headers, json=body
    )
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def _animal_and_eggs(client: AsyncClient, authed: AuthedUser) -> tuple[int, int]:
    asset_id = await _create_asset(client, authed, ANIMAL_AGGREGATED)
    cat_id = await _category(client, authed, "production", "Huevos", "unit")
    return asset_id, cat_id


class TestCreate:
    async def test_create_per_head_continuous_target(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, cat_id),
        )

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["basis"] == "per_head_continuous"
        assert body["period"] == "day"
        assert Decimal(body["expected_rate"]) == Decimal("0.8")

    async def test_total_target_on_crop_ok(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, CROP_AGGREGATED)
        cat_id = await _category(client, authed_user, "production", "Grano", "kg")

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, cat_id, basis="total", period=None, expected_rate="500"),
        )

        assert resp.status_code == 201, resp.text


class TestCreateRejections:
    async def test_per_head_continuous_requires_period(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, cat_id, period=None),
        )
        assert resp.status_code == 422

    async def test_period_only_for_continuous(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, cat_id, basis="per_event"),
        )
        assert resp.status_code == 422

    async def test_effective_to_before_from_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(
                asset_id,
                cat_id,
                basis="total",
                period=None,
                effective_from="2026-06-01",
                effective_to="2026-01-01",
            ),
        )
        assert resp.status_code == 422

    async def test_per_head_continuous_requires_animal_asset(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        crop_id = await _create_asset(client, authed_user, CROP_AGGREGATED)
        cat_id = await _category(client, authed_user, "production", "Huevos", "unit")

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(crop_id, cat_id),
        )
        assert resp.status_code == 422

    async def test_category_must_be_production(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        expense = await _category(client, authed_user, "expense", "Feed")

        resp = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, expense, basis="total", period=None),
        )
        assert resp.status_code == 422

    async def test_duplicate_target_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)
        body = _payload(asset_id, cat_id)
        first = await client.post(
            targets_url(authed_user.farm_id), headers=authed_user.headers, json=body
        )
        assert first.status_code == 201

        duplicate = await client.post(
            targets_url(authed_user.farm_id), headers=authed_user.headers, json=body
        )
        assert duplicate.status_code == 409


class TestListUpdateDelete:
    async def test_filter_by_asset(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_a = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        asset_b = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        cat_id = await _category(client, authed_user, "production", "Huevos", "unit")
        for asset_id in (asset_a, asset_b):
            await client.post(
                targets_url(authed_user.farm_id),
                headers=authed_user.headers,
                json=_payload(asset_id, cat_id),
            )

        resp = await client.get(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            params={"asset_id": asset_a},
        )
        assert resp.json()["meta"]["total"] == 1

    async def test_update_expected_rate(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)
        created = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, cat_id),
        )
        target_id = created.json()["id"]

        resp = await client.patch(
            target_url(authed_user.farm_id, target_id),
            headers=authed_user.headers,
            json={"expected_rate": "0.9"},
        )
        assert resp.status_code == 200
        assert Decimal(resp.json()["expected_rate"]) == Decimal("0.9")

    async def test_delete(self, client: AsyncClient, authed_user: AuthedUser) -> None:
        asset_id, cat_id = await _animal_and_eggs(client, authed_user)
        created = await client.post(
            targets_url(authed_user.farm_id),
            headers=authed_user.headers,
            json=_payload(asset_id, cat_id),
        )
        target_id = created.json()["id"]

        deleted = await client.delete(
            target_url(authed_user.farm_id, target_id), headers=authed_user.headers
        )
        assert deleted.status_code == 204

        follow_up = await client.get(
            target_url(authed_user.farm_id, target_id), headers=authed_user.headers
        )
        assert follow_up.status_code == 404


class TestFarmScope:
    async def test_non_member_cannot_list(
        self,
        client: AsyncClient,
        register_user: Callable[[str], Awaitable[AuthedUser]],
    ) -> None:
        alice = await register_user("alice@example.com")
        bob = await register_user("bob@example.com")

        resp = await client.get(targets_url(alice.farm_id), headers=bob.headers)
        assert resp.status_code == 403
