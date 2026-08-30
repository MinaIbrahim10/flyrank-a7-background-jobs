import unittest
from unittest.mock import patch

import httpx

import app as application


class AppTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        application.reports.clear()
        transport = httpx.ASGITransport(app=application.app)
        self.client = httpx.AsyncClient(transport=transport, base_url="http://test")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_health(self) -> None:
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @patch.object(application.inngest_client, "send", return_value=["event-id"])
    async def test_create_and_get_report(self, send) -> None:
        created = await self.client.post("/reports", json={"topic": "space"})
        self.assertEqual(created.status_code, 202)
        body = created.json()
        self.assertEqual(body["status"], "pending")

        saved = await self.client.get(f"/reports/{body['id']}")
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["topic"], "space")
        self.assertEqual(saved.json()["status"], "pending")
        send.assert_awaited_once()

    async def test_unknown_report(self) -> None:
        response = await self.client.get("/reports/missing")
        self.assertEqual(response.status_code, 404)

    async def test_missing_and_blank_topics_do_not_enqueue(self) -> None:
        with patch.object(application.inngest_client, "send") as send:
            for body in ({}, {"topic": ""}, {"topic": "   "}, {"topic": None}):
                with self.subTest(body=body):
                    response = await self.client.post("/reports", json=body)
                    self.assertEqual(response.status_code, 400)
            send.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
