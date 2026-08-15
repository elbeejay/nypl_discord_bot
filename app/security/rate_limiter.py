"""
In-Memory Sliding Window Rate Limiter Middleware & Dependencies.
Protects endpoints against brute-force, scraping, and denial-of-service spam.
Features bounded memory tracking (LRU/OrderedDict) to prevent OOM memory exhaustion.
"""

import time
import logging
from collections import OrderedDict
from typing import List, Tuple
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    def __init__(self, limit_per_minute: int = 60, max_tracked_ips: int = 10000):
        self.limit = limit_per_minute
        self.window_seconds = 60
        self.max_tracked_ips = max_tracked_ips
        self._ip_requests: OrderedDict[str, List[float]] = OrderedDict()
        self._last_cleanup = time.time()

    def get_client_ip(self, request: Request) -> str:
        """
        Extracts client IP safely.
        On Google Cloud Run, trusted reverse proxy appends the verified client IP.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
            if ips:
                # Rightmost IP in X-Forwarded-For is the one appended by the nearest trusted infrastructure proxy
                return ips[-1]
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def is_rate_limited(self, ip: str, custom_limit: int = None) -> Tuple[bool, int]:
        """
        Checks if the given IP exceeds the allowed rate limit.
        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()
        self._maybe_cleanup(now)

        limit = custom_limit or self.limit
        requests = self._ip_requests.get(ip, [])

        # Filter out requests older than the sliding window (60s)
        window_start = now - self.window_seconds
        valid_requests = [t for t in requests if t > window_start]

        if len(valid_requests) >= limit:
            oldest_in_window = valid_requests[0]
            retry_after = int((oldest_in_window + self.window_seconds) - now) + 1
            return True, max(1, retry_after)

        valid_requests.append(now)

        # Enforce memory bound: if cap is reached, evict oldest entry
        if len(self._ip_requests) >= self.max_tracked_ips and ip not in self._ip_requests:
            self._ip_requests.popitem(last=False)

        self._ip_requests[ip] = valid_requests
        self._ip_requests.move_to_end(ip)
        return False, 0

    def _maybe_cleanup(self, now: float):
        """Evicts IPs with no recent activity every 2 minutes."""
        if now - self._last_cleanup > 120:
            window_start = now - self.window_seconds
            expired_ips = [
                ip for ip, reqs in self._ip_requests.items()
                if not reqs or reqs[-1] <= window_start
            ]
            for ip in expired_ips:
                self._ip_requests.pop(ip, None)
            self._last_cleanup = now


rate_limiter = SlidingWindowRateLimiter(limit_per_minute=settings.RATE_LIMIT_PER_MINUTE)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware.
    Enforces per-IP limits across all endpoints.
    """
    async def dispatch(self, request: Request, call_next):
        # Allow internal health checks higher throughput if needed
        limit = settings.RATE_LIMIT_PER_MINUTE
        if request.url.path == "/health":
            limit = settings.RATE_LIMIT_PER_MINUTE * 4

        client_ip = rate_limiter.get_client_ip(request)
        is_limited, retry_after = rate_limiter.is_rate_limited(client_ip, custom_limit=limit)

        if is_limited:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit of {limit} req/min exceeded. Please slow down.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
