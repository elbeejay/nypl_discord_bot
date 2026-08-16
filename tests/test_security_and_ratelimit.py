import unittest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings
from app.security.rate_limiter import SlidingWindowRateLimiter


class TestSecurityAndAuth(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        settings.FRONTEND_ACCESS_PASSCODE = None
        settings.FRONTEND_API_KEY = None
        settings.ENVIRONMENT = "development"
        self.transport = ASGITransport(app=app)
        self.client = AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self):
        # Reset security settings
        settings.FRONTEND_ACCESS_PASSCODE = None
        settings.FRONTEND_API_KEY = None
        settings.ENVIRONMENT = "development"
        await self.client.aclose()

    async def test_api_key_auth_enforcement(self):
        # 1. No key required when neither passcode nor key is set
        settings.FRONTEND_ACCESS_PASSCODE = None
        settings.FRONTEND_API_KEY = None
        res = await self.client.get("/api/v1/a2ui/catalog")
        self.assertEqual(res.status_code, 200)

        # 2. Passcode enforcement enabled
        settings.FRONTEND_ACCESS_PASSCODE = "secure-test-token-xyz"

        # Missing key/cookie -> 401
        res_missing = await self.client.get("/api/v1/a2ui/catalog")
        self.assertEqual(res_missing.status_code, 401)

        # Invalid key -> 401
        res_invalid = await self.client.get("/api/v1/a2ui/catalog", headers={"X-API-Key": "wrong-key"})
        self.assertEqual(res_invalid.status_code, 401)

        # Valid X-API-Key header -> 200
        res_header = await self.client.get("/api/v1/a2ui/catalog", headers={"X-API-Key": "secure-test-token-xyz"})
        self.assertEqual(res_header.status_code, 200)

        # Valid Authorization Bearer header -> 200
        res_bearer = await self.client.get("/api/v1/a2ui/catalog", headers={"Authorization": "Bearer secure-test-token-xyz"})
        self.assertEqual(res_bearer.status_code, 200)

        # 3. Session Login with HttpOnly cookie
        login_res = await self.client.post("/api/v1/auth/login", json={"passcode": "secure-test-token-xyz"})
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("nypl_session", login_res.cookies)

        # Use the session cookie -> 200 without X-API-Key header
        res_cookie = await self.client.get("/api/v1/a2ui/catalog", cookies=login_res.cookies)
        self.assertEqual(res_cookie.status_code, 200)

        # Verify endpoint returns 200 with cookie
        verify_res = await self.client.get("/api/v1/auth/verify", cookies=login_res.cookies)
        self.assertEqual(verify_res.status_code, 200)


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
        settings.ENVIRONMENT = "production"
        res_prod = await self.client.get("/")
        self.assertEqual(res_prod.status_code, 200)
        self.assertEqual(res_prod.json(), {"status": "healthy", "service": "nypl_discord_bot"})

        # Legacy /chat endpoint should return 404 in production with or without body
        res_chat = await self.client.post("/chat", json={"query": "hello"})
        self.assertEqual(res_chat.status_code, 404)

        res_chat_empty = await self.client.post("/chat")
        self.assertEqual(res_chat_empty.status_code, 404)

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

    async def test_path_traversal_prevention(self):
        # Attempting directory traversal via the static SPA handler must not serve sensitive root files
        res_traversal = await self.client.get("/../requirements.txt")
        # Should return SPA index.html or API status, NOT raw requirements.txt content
        self.assertNotIn("pydantic-settings", res_traversal.text)

        res_traversal2 = await self.client.get("/../../app/config.py")
        self.assertNotIn("SettingsConfigDict", res_traversal2.text)

    async def test_unconfigured_passcode_login(self):
        settings.FRONTEND_ACCESS_PASSCODE = None
        settings.FRONTEND_API_KEY = None
        login_res = await self.client.post("/api/v1/auth/login", json={"passcode": "any-passcode"})
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("nypl_session", login_res.cookies)


if __name__ == "__main__":
    unittest.main()
