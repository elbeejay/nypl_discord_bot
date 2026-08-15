import asyncio
import unittest
from httpx import AsyncClient, ASGITransport
from nacl.signing import SigningKey

from app.main import app, extract_query_from_options
from app.config import settings
from app.discord.security import verify_discord_signature
from app.tools.nypl_api import find_nypl_branch
from app.tools.socrata import DATASETS


class TestDiscordBot(unittest.TestCase):
    def setUp(self):
        self.signing_key = SigningKey.generate()
        self.public_key_hex = self.signing_key.verify_key.encode().hex()
        settings.DISCORD_PUBLIC_KEY = self.public_key_hex
        settings.DISCORD_APP_ID = "1234567890"

    def test_extract_options(self):
        self.assertEqual(extract_query_from_options(None), "Hello!")
        self.assertEqual(extract_query_from_options([]), "Hello!")
        self.assertEqual(
            extract_query_from_options([{"name": "query", "value": "Astoria 311 complaints"}]),
            "Astoria 311 complaints"
        )
        self.assertEqual(
            extract_query_from_options([
                {
                    "name": "search",
                    "options": [{"name": "query", "value": "Schwarzman reading room"}]
                }
            ]),
            "Schwarzman reading room"
        )

    def test_signature_verification(self):
        timestamp = "1700000000"
        body = b'{"type": 1}'
        valid_sig = self.signing_key.sign(timestamp.encode() + body).signature.hex()
        
        # Valid signature
        self.assertTrue(verify_discord_signature(valid_sig, timestamp, body))
        
        # Invalid signature
        self.assertFalse(verify_discord_signature("00" * 64, timestamp, body))
        
        # Tampered body
        self.assertFalse(verify_discord_signature(valid_sig, timestamp, b'{"type": 2}'))

    def test_nypl_branch_tool(self):
        res = asyncio.run(find_nypl_branch("Schwarzman"))
        self.assertIn("Stephen A. Schwarzman Building", res)
        self.assertIn("Rose Main Reading Room", res)

    def test_socrata_dataset_constants(self):
        self.assertIn("311_service_requests", DATASETS)
        self.assertIn("restaurant_inspections", DATASETS)
        self.assertIn("tree_census_2015", DATASETS)


class TestFastAPIEndpoints(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.signing_key = SigningKey.generate()
        self.public_key_hex = self.signing_key.verify_key.encode().hex()
        settings.DISCORD_PUBLIC_KEY = self.public_key_hex
        settings.DISCORD_APP_ID = "1234567890"
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_root_endpoint(self):
        response = await self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "nypl_discord_bot")

    async def test_health_check_endpoint(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    async def test_discord_ping_type_1(self):
        body = b'{"type": 1}'
        timestamp = "1700000000"
        sig = self.signing_key.sign(timestamp.encode() + body).signature.hex()
        headers = {
            "X-Signature-Ed25519": sig,
            "X-Signature-Timestamp": timestamp,
            "Content-Type": "application/json",
        }
        response = await self.client.post("/interactions", content=body, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"type": 1})

    async def test_discord_slash_command_deferred_type_5(self):
        body = b'{"type": 2, "token": "test_interaction_token", "data": {"name": "ask", "options": [{"name": "query", "value": "Test query"}]}}'
        timestamp = "1700000000"
        sig = self.signing_key.sign(timestamp.encode() + body).signature.hex()
        headers = {
            "X-Signature-Ed25519": sig,
            "X-Signature-Timestamp": timestamp,
            "Content-Type": "application/json",
        }
        response = await self.client.post("/interactions", content=body, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"type": 5})

    async def test_local_chat_endpoint(self):
        response = await self.client.post("/chat", json={"query": "Hello test", "command": "ask"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["query"], "Hello test")
        self.assertIn("response", data)


if __name__ == "__main__":
    unittest.main()
