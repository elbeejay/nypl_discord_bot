import unittest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings
from app.security.rate_limiter import SlidingWindowRateLimiter


class TestSecurityAndAuth(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self):
        # Reset security settings
        settings.FRONTEND_API_KEY = None
        settings.ENVIRONMENT = "development"
        await self.client.aclose()

    async def test_api_key_auth_enforcement(self):
        # 1. No key required in development mode by default
        settings.FRONTEND_API_KEY = None
        res = await self.client.get("/api/v1/a2ui/catalog")
        self.assertEqual(res.status_code, 200)

        # 2. Key enforcement enabled
        settings.FRONTEND_API_KEY = "secure-test-token-xyz"

        # Missing key -> 401
        res_missing = await self.client.get("/api/v1/a2ui/catalog")
        self.assertEqual(res_missing.status_code, 401)
        self.assertIn("Missing API Key", res_missing.json()["detail"])

        # Invalid key -> 401
        res_invalid = await self.client.get("/api/v1/a2ui/catalog", headers={"X-API-Key": "wrong-key"})
        self.assertEqual(res_invalid.status_code, 401)
        self.assertIn("Invalid API Key", res_invalid.json()["detail"])

        # Valid X-API-Key header -> 200
        res_header = await self.client.get("/api/v1/a2ui/catalog", headers={"X-API-Key": "secure-test-token-xyz"})
        self.assertEqual(res_header.status_code, 200)

        # Valid Authorization Bearer header -> 200
        res_bearer = await self.client.get("/api/v1/a2ui/catalog", headers={"Authorization": "Bearer secure-test-token-xyz"})
        self.assertEqual(res_bearer.status_code, 200)

        # Valid ?api_key= query param -> 200
        res_param = await self.client.get("/api/v1/a2ui/catalog?api_key=secure-test-token-xyz")
        self.assertEqual(res_param.status_code, 200)

    async def test_production_lockdown(self):
        # Test Development Mode
        settings.ENVIRONMENT = "development"
        res_dev = await self.client.get("/")
        self.assertEqual(res_dev.status_code, 200)
        self.assertIn("models", res_dev.json())

        # Test Production Mode
        import app.main as main_mod
        main_mod.is_production = True
        try:
            res_prod = await self.client.get("/")
            self.assertEqual(res_prod.status_code, 200)
            self.assertEqual(res_prod.json(), {"status": "healthy", "service": "nypl_discord_bot"})

            # Legacy /chat endpoint should return 404 in production
            res_chat = await self.client.post("/chat", json={"query": "hello"})
            self.assertEqual(res_chat.status_code, 404)
        finally:
            main_mod.is_production = False

    def test_sliding_window_rate_limiter(self):
        limiter = SlidingWindowRateLimiter(limit_per_minute=3)
        ip = "192.168.1.100"

        # First 3 requests allowed
        is_lim, _ = limiter.is_rate_limited(ip)
        self.assertFalse(is_lim)
        is_lim, _ = limiter.is_rate_limited(ip)
        self.assertFalse(is_lim)
        is_lim, _ = limiter.is_rate_limited(ip)
        self.assertFalse(is_lim)

        # 4th request blocked with 429
        is_lim, retry_after = limiter.is_rate_limited(ip)
        self.assertTrue(is_lim)
        self.assertTrue(retry_after > 0)


if __name__ == "__main__":
    unittest.main()
