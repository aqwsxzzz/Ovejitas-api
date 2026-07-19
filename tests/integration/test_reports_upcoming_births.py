"""Stage 5 — upcoming-births alert window report.

Returns individuals whose latest pregnancy check says pregnant with a due date
inside [date_from, date_to]. A later not-pregnant check suppresses the alert.
"""

from httpx import AsyncClient

from tests.conftest import AuthedUser

ANIMAL_INDIVIDUAL = {"name": "Ovejas", "kind": "animal", "mode": "individual"}
WINDOW = {"date_from": "2026-11-01T00:00:00Z", "date_to": "2026-11-30T00:00:00Z"}


def _assets_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/assets"


def _pregnancies_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/pregnancies"


def _report_url(farm_id: int) -> str:
    return f"/api/v1/farms/{farm_id}/reports/upcoming-births"


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


async def _check(
    client: AsyncClient,
    authed: AuthedUser,
    individual_id: int,
    *,
    occurred_at: str,
    is_pregnant: bool,
    due: str | None,
) -> None:
    payload: dict = {
        "individual_id": individual_id,
        "occurred_at": occurred_at,
        "is_pregnant": is_pregnant,
        "expected_due_at": due,
    }
    resp = await client.post(_pregnancies_url(authed.farm_id), headers=authed.headers, json=payload)
    assert resp.status_code == 201, resp.text


class TestUpcomingBirths:
    async def test_lists_individual_due_inside_window(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        ewe = await _individual(client, authed_user, "E-1")
        await _check(
            client,
            authed_user,
            ewe,
            occurred_at="2026-06-10T10:00:00Z",
            is_pregnant=True,
            due="2026-11-15T00:00:00Z",
        )

        resp = await client.get(
            _report_url(authed_user.farm_id), headers=authed_user.headers, params=WINDOW
        )

        assert resp.status_code == 200, resp.text
        rows = resp.json()["data"]
        assert [r["individual_id"] for r in rows] == [ewe]
        assert rows[0]["days_until_due"] == 14

    async def test_excludes_due_outside_window(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        ewe = await _individual(client, authed_user, "E-2")
        await _check(
            client,
            authed_user,
            ewe,
            occurred_at="2026-06-10T10:00:00Z",
            is_pregnant=True,
            due="2027-02-01T00:00:00Z",
        )

        resp = await client.get(
            _report_url(authed_user.farm_id), headers=authed_user.headers, params=WINDOW
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["data"] == []

    async def test_later_not_pregnant_check_suppresses_alert(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        ewe = await _individual(client, authed_user, "E-3")
        await _check(
            client,
            authed_user,
            ewe,
            occurred_at="2026-06-10T10:00:00Z",
            is_pregnant=True,
            due="2026-11-15T00:00:00Z",
        )
        await _check(
            client,
            authed_user,
            ewe,
            occurred_at="2026-07-01T10:00:00Z",
            is_pregnant=False,
            due=None,
        )

        resp = await client.get(
            _report_url(authed_user.farm_id), headers=authed_user.headers, params=WINDOW
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["data"] == []

    async def test_window_dates_are_required(
        self, client: AsyncClient, authed_user: AuthedUser
    ) -> None:
        resp = await client.get(_report_url(authed_user.farm_id), headers=authed_user.headers)

        assert resp.status_code == 422
