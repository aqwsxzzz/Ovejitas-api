"""Currency resource — CRUD, ISO validation, frozen code, archive."""

from httpx import AsyncClient

from tests.conftest import AuthedUser


def currencies(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/currencies"


class TestCurrencyCreate:
    async def test_create_supported_code_returns_201(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "ARS", "name": "Argentine Peso", "symbol": "$"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["code"] == "ARS"
        assert body["name"] == "Argentine Peso"
        assert body["archived_at"] is None

    async def test_lowercase_code_is_uppercased(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "uyu", "name": "Peso"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["code"] == "UYU"

    async def test_unsupported_code_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "XYZ", "name": "Nope"},
        )
        assert resp.status_code == 422

    async def test_duplicate_code_conflicts(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        # USD already exists (seeded at farm registration).
        resp = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "USD", "name": "Dollar"},
        )
        assert resp.status_code == 409, resp.text


class TestCurrencyUpdate:
    async def test_patch_name_and_symbol(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "BRL", "name": "Real"},
        )
        cid = created.json()["id"]
        resp = await client.patch(
            f"{currencies(authed_user.farm_id)}/{cid}",
            headers=authed_user.headers,
            json={"name": "Brazilian Real", "symbol": "R$"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["name"] == "Brazilian Real"
        assert resp.json()["symbol"] == "R$"

    async def test_code_is_frozen_and_rejected_in_patch(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "CLP", "name": "Peso"},
        )
        cid = created.json()["id"]
        resp = await client.patch(
            f"{currencies(authed_user.farm_id)}/{cid}",
            headers=authed_user.headers,
            json={"code": "USD"},
        )
        assert resp.status_code == 422


class TestCurrencyArchive:
    async def test_delete_archives_and_hides_from_active_list(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        created = await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "PEN", "name": "Sol"},
        )
        cid = created.json()["id"]

        deleted = await client.delete(
            f"{currencies(authed_user.farm_id)}/{cid}", headers=authed_user.headers
        )
        assert deleted.status_code == 204

        # Still retrievable (history intact), but flagged archived.
        one = await client.get(
            f"{currencies(authed_user.farm_id)}/{cid}", headers=authed_user.headers
        )
        assert one.json()["archived_at"] is not None

        active = await client.get(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            params={"archived": "false"},
        )
        assert cid not in [c["id"] for c in active.json()["data"]]


class TestCurrencyScope:
    async def test_currencies_are_isolated_per_farm(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user,
    ) -> None:
        other = await register_user("other@example.com")
        await client.post(
            currencies(authed_user.farm_id),
            headers=authed_user.headers,
            json={"code": "COP", "name": "Peso"},
        )
        listing = await client.get(currencies(other.farm_id), headers=other.headers)
        assert "COP" not in [c["code"] for c in listing.json()["data"]]

    async def test_non_member_forbidden(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user,
    ) -> None:
        intruder = await register_user("intruder@example.com")
        resp = await client.get(currencies(authed_user.farm_id), headers=intruder.headers)
        assert resp.status_code == 403
