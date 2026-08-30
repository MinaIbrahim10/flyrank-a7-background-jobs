from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.store import reports


@pytest.fixture(autouse=True)
def clear_reports():
    reports.clear()
    yield
    reports.clear()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client


@pytest.mark.anyio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [{}, {"topic": ""}, {"topic": "   "}, {"topic": 7}])
async def test_invalid_topics_are_rejected_before_event(client, payload):
    with patch("app.main.inngest_client.send", new_callable=AsyncMock) as send:
        response = await client.post("/reports", json=payload)
    assert response.status_code == 400
    send.assert_not_awaited()


@pytest.mark.anyio
async def test_create_and_get_pending_report(client):
    with patch("app.main.inngest_client.send", new_callable=AsyncMock) as send:
        response = await client.post("/reports", json={"topic": "durable jobs"})

    assert response.status_code == 202
    body = response.json()
    UUID(body["id"])
    assert body == {"id": body["id"], "status": "pending"}
    send.assert_awaited_once()

    fetched = await client.get(f"/reports/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == {
        "id": body["id"],
        "topic": "durable jobs",
        "status": "pending",
    }


@pytest.mark.anyio
async def test_unknown_report_is_404(client):
    response = await client.get("/reports/unknown")
    assert response.status_code == 404

