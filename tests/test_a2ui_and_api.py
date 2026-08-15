import unittest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agents.session_manager import session_manager
from app.tools.a2ui_generator import (
    build_chart_component,
    build_map_component,
    build_metric_card_component,
    build_photo_gallery_component,
    build_table_component,
    extract_a2ui_from_text_response,
)


class TestA2UIComponents(unittest.TestCase):
    def test_chart_builder(self):
        comp = build_chart_component(
            title="311 Complaints by Category",
            labels=["Noise", "Illegal Parking", "Heat/Hot Water"],
            data=[45.0, 30.0, 25.0],
            chart_type="doughnut",
        )
        self.assertEqual(comp.type, "chart")
        self.assertEqual(comp.data.chart_type, "doughnut")
        self.assertEqual(len(comp.data.labels), 3)
        self.assertEqual(comp.data.datasets[0].data, [45.0, 30.0, 25.0])

    def test_map_builder(self):
        comp = build_map_component(
            title="NYPL Branches",
            markers=[
                {"title": "Schwarzman", "lat": 40.7532, "lng": -73.9822, "category": "library"},
                {"title": "Schomburg", "lat": 40.8144, "lng": -73.9419, "category": "library"},
            ]
        )
        self.assertEqual(comp.type, "map")
        self.assertEqual(len(comp.data.markers), 2)
        self.assertAlmostEqual(comp.data.markers[0].lat, 40.7532)

    def test_metric_card_builder(self):
        comp = build_metric_card_component(
            title="Astoria 311 Summary",
            metrics=[
                {"label": "Total Complaints", "value": "120", "delta": "+5%", "status": "warning"},
                {"label": "Open Cases", "value": "4", "status": "critical"},
            ]
        )
        self.assertEqual(comp.type, "metric_card")
        self.assertEqual(len(comp.data.metrics), 2)
        self.assertEqual(comp.data.metrics[0].value, "120")

    def test_photo_gallery_builder(self):
        comp = build_photo_gallery_component(
            title="Subway Archives",
            photos=[
                {"title": "1930s Construction", "image_url": "https://images.nypl.org/123", "link": "https://digitalcollections.nypl.org/items/123"}
            ]
        )
        self.assertEqual(comp.type, "photo_gallery")
        self.assertEqual(len(comp.data.items), 1)

    def test_table_builder(self):
        comp = build_table_component(
            title="Restaurant Inspections",
            columns=["Name", "Grade", "Score"],
            rows=[["Shake Shack", "A", 10], ["Katz's", "A", 8]],
        )
        self.assertEqual(comp.type, "data_table")
        self.assertEqual(len(comp.data.rows), 2)

    def test_a2ui_text_extractor(self):
        sample_nypl_text = (
            "Here are archive items: [Brooklyn Bridge Arch](https://digitalcollections.nypl.org/items/510d47e1-e341-a3d9-e040-e00a18064a99) "
            "and [Subway View](https://digitalcollections.nypl.org/items/510d47e1-e342-a3d9-e040-e00a18064a99)"
        )
        payload = extract_a2ui_from_text_response(sample_nypl_text, command_name="nypl")
        self.assertIsNotNone(payload)
        self.assertTrue(len(payload.components) > 0)
        self.assertEqual(payload.components[0].type, "photo_gallery")


class TestFrontendAPIEndpoints(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_a2ui_catalog(self):
        response = await self.client.get("/api/v1/a2ui/catalog")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version"], "1.0")
        self.assertIn("supported_components", data)
        types = [c["type"] for c in data["supported_components"]]
        self.assertIn("chart", types)
        self.assertIn("map", types)
        self.assertIn("photo_gallery", types)

    async def test_frontend_chat_rest(self):
        response = await self.client.post(
            "/api/v1/chat",
            json={"query": "Hello test query", "command": "ask", "enable_a2ui": True}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("session_id", data)
        self.assertIn("response", data)
        self.assertEqual(data["query"], "Hello test query")

        session_id = data["session_id"]
        # Test session retrieval
        sess_resp = await self.client.get(f"/api/v1/sessions/{session_id}")
        self.assertEqual(sess_resp.status_code, 200)
        sess_data = sess_resp.json()
        self.assertEqual(sess_data["session_id"], session_id)
        self.assertTrue(len(sess_data["messages"]) >= 2)

        # Test session delete
        del_resp = await self.client.delete(f"/api/v1/sessions/{session_id}")
        self.assertEqual(del_resp.status_code, 200)

    async def test_frontend_chat_sse_stream(self):
        response = await self.client.post(
            "/api/v1/chat/stream",
            json={"query": "Hello test streaming", "command": "ask"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers["content-type"])
        content = response.text
        self.assertIn("event: status", content)
        self.assertIn("event: token", content)
        self.assertIn("event: done", content)


if __name__ == "__main__":
    unittest.main()
