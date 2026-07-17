"""Per-event currency of record — fallback, validation, and no-restamp."""

from decimal import Decimal

from httpx import AsyncClient, Response

from tests.conftest import AuthedUser


def currencies(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/currencies"


async def _asset(client: AsyncClient, user: AuthedUser) -> int:
    resp = await client.post(
        f"/api/v1/farms/{user.farm_id}/assets",
        headers=user.headers,
        json={"name": "Crop", "kind": "crop", "mode": "aggregated"},
    )
    return int(resp.json()["id"])


async def _currency_id(client: AsyncClient, user: AuthedUser, code: str) -> int:
    listing = await client.get(currencies(user.farm_id), headers=user.headers)
    for c in listing.json()["data"]:
        if c["code"] == code:
            return int(c["id"])
    created = await client.post(
        currencies(user.farm_id), headers=user.headers, json={"code": code, "name": code}
    )
    return int(created.json()["id"])


async def _expense(
    client: AsyncClient, user: AuthedUser, asset_id: int, amount: str, **extra: object
) -> Response:
    return await client.post(
        f"/api/v1/farms/{user.farm_id}/assets/{asset_id}/events",
        headers=user.headers,
        json={"type": "expense", "occurred_at": "2026-04-01T00:00:00Z", "amount": amount, **extra},
    )


class TestCurrencyOfRecord:
    async def test_expense_records_chosen_currency(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user)
        ars = await _currency_id(client, authed_user, "ARS")

        resp = await _expense(client, authed_user, asset_id, "500", currency_id=ars)

        assert resp.status_code == 201, resp.text
        assert resp.json()["currency_id"] == ars

    async def test_expense_without_currency_uses_farm_default(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user)
        usd = await _currency_id(client, authed_user, "USD")

        resp = await _expense(client, authed_user, asset_id, "42")

        assert resp.status_code == 201, resp.text
        assert resp.json()["currency_id"] == usd

    async def test_foreign_farm_currency_rejected(
        self,
        client: AsyncClient,
        authed_user: AuthedUser,
        register_user,
    ) -> None:
        other = await register_user("other@example.com")
        other_usd = await _currency_id(client, other, "USD")
        asset_id = await _asset(client, authed_user)

        resp = await _expense(client, authed_user, asset_id, "10", currency_id=other_usd)

        assert resp.status_code == 404, resp.text

    async def test_archived_currency_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user)
        ars = await _currency_id(client, authed_user, "ARS")
        await client.delete(f"{currencies(authed_user.farm_id)}/{ars}", headers=authed_user.headers)

        resp = await _expense(client, authed_user, asset_id, "10", currency_id=ars)

        assert resp.status_code == 422, resp.text


class TestNoRestamp:
    async def test_changing_default_leaves_existing_events_untouched(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user)
        usd = await _currency_id(client, authed_user, "USD")
        first = await _expense(client, authed_user, asset_id, "100")
        assert first.json()["currency_id"] == usd

        # Switch the farm's preferred currency; history must not re-stamp.
        await client.patch(
            f"/api/v1/farms/{authed_user.farm_id}",
            headers=authed_user.headers,
            json={"default_currency": "ARS"},
        )
        ars = await _currency_id(client, authed_user, "ARS")
        second = await _expense(client, authed_user, asset_id, "200")

        assert first.json()["currency_id"] == usd  # unchanged
        assert second.json()["currency_id"] == ars  # new default applies going forward


class TestPerCurrencySeparation:
    async def test_profitability_never_sums_across_currencies(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _asset(client, authed_user)
        usd = await _currency_id(client, authed_user, "USD")
        ars = await _currency_id(client, authed_user, "ARS")
        await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/events",
            headers=authed_user.headers,
            json={
                "type": "income",
                "occurred_at": "2026-04-01T00:00:00Z",
                "amount": "300",
                "currency_id": usd,
            },
        )
        await client.post(
            f"/api/v1/farms/{authed_user.farm_id}/assets/{asset_id}/events",
            headers=authed_user.headers,
            json={
                "type": "income",
                "occurred_at": "2026-04-01T00:00:00Z",
                "amount": "1000",
                "currency_id": ars,
            },
        )

        resp = await client.get(
            f"/api/v1/farms/{authed_user.farm_id}/reports/profitability",
            headers=authed_user.headers,
        )
        rows = {r["currency"]: r for r in resp.json()["data"]}
        assert set(rows) == {"USD", "ARS"}
        assert Decimal(rows["USD"]["income_total"]) == Decimal("300")
        assert Decimal(rows["ARS"]["income_total"]) == Decimal("1000")
