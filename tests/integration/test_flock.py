from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_AGGREGATED = {"name": "Gallinas", "kind": "animal", "mode": "aggregated"}
ANIMAL_INDIVIDUAL = {"name": "Vacas", "kind": "animal", "mode": "individual"}
MATERIAL_AGGREGATED = {"name": "Maíz", "kind": "material", "mode": "aggregated"}


def assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def flock_url(farm_id: int, asset_id: int, action: str) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/flock/{action}"


def events_url(farm_id: int, asset_id: int) -> str:
    return f"{assets_url(farm_id)}/{asset_id}/events"


async def _create_asset(client: AsyncClient, authed: AuthedUser, body: dict[str, str]) -> int:
    resp = await client.post(assets_url(authed.farm_id), headers=authed.headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _events(
    client: AsyncClient, authed: AuthedUser, asset_id: int, event_type: str
) -> list[dict[str, object]]:
    resp = await client.get(
        events_url(authed.farm_id, asset_id),
        headers=authed.headers,
        params={"type": event_type},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


async def _flock(
    client: AsyncClient, authed: AuthedUser, asset_id: int, action: str, body: dict[str, object]
) -> object:
    return await client.post(
        flock_url(authed.farm_id, asset_id, action), headers=authed.headers, json=body
    )


class TestFlockAcquisition:
    async def test_acquisition_increments_headcount(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        resp = await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 20})

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["headcount"] == "20"
        assert body["paired_event_id"] is None
        increments = await _events(client, authed_user, asset_id, "inventory")
        assert len(increments) == 1
        assert increments[0]["unit"] == "head"

    async def test_acquisition_with_amount_books_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        resp = await _flock(
            client, authed_user, asset_id, "acquisitions", {"quantity": 20, "amount": "300.00"}
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["paired_event_id"] is not None
        expenses = await _events(client, authed_user, asset_id, "expense")
        assert len(expenses) == 1
        assert expenses[0]["amount"] == "300.00"

    async def test_acquisition_without_amount_books_no_expense(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 20})

        assert await _events(client, authed_user, asset_id, "expense") == []


class TestFlockSale:
    async def test_sale_decrements_headcount_and_books_income(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 20})

        resp = await _flock(
            client, authed_user, asset_id, "sales", {"quantity": 8, "amount": "120.00"}
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["headcount"] == "12"
        income = await _events(client, authed_user, asset_id, "income")
        assert len(income) == 1
        assert income[0]["amount"] == "120.00"

    async def test_sale_without_amount_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 20})

        resp = await _flock(client, authed_user, asset_id, "sales", {"quantity": 5})

        assert resp.status_code == 422

    async def test_overselling_rejected_and_writes_nothing(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 5})

        resp = await _flock(
            client, authed_user, asset_id, "sales", {"quantity": 10, "amount": "50.00"}
        )

        assert resp.status_code == 409
        assert await _events(client, authed_user, asset_id, "income") == []
        # the acquisition increment survives; the sale decrement was rolled back
        assert len(await _events(client, authed_user, asset_id, "inventory")) == 1


class TestFlockMortality:
    async def test_mortality_decrements_headcount_and_emits_event(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 20})

        resp = await _flock(
            client, authed_user, asset_id, "mortalities", {"quantity": 3, "cause": "fox"}
        )

        assert resp.status_code == 201, resp.text
        assert resp.json()["headcount"] == "17"
        deaths = await _events(client, authed_user, asset_id, "mortality")
        assert len(deaths) == 1
        assert deaths[0]["quantity"] == "3"

    async def test_over_culling_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)
        await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 2})

        resp = await _flock(client, authed_user, asset_id, "mortalities", {"quantity": 5})

        assert resp.status_code == 409
        assert await _events(client, authed_user, asset_id, "mortality") == []


class TestFlockRejections:
    async def test_individual_mode_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_INDIVIDUAL)

        resp = await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 10})

        assert resp.status_code == 422

    async def test_non_animal_asset_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, MATERIAL_AGGREGATED)

        resp = await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 10})

        assert resp.status_code == 422

    async def test_fractional_quantity_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        resp = await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 2.5})

        assert resp.status_code == 422

    async def test_zero_quantity_rejected(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        asset_id = await _create_asset(client, authed_user, ANIMAL_AGGREGATED)

        resp = await _flock(client, authed_user, asset_id, "acquisitions", {"quantity": 0})

        assert resp.status_code == 422
