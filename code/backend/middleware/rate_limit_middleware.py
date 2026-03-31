"""
Rate limiting middleware for API protection
"""

import logging
import time
from typing import Any, Callable

from config.database import get_redis
from config.settings import settings
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis for distributed rate limiting
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.rate_limit_per_minute = settings.security.RATE_LIMIT_PER_MINUTE
        self.rate_limit_burst = settings.security.RATE_LIMIT_BURST

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting
        """
        if self._should_skip_rate_limit(request):
            return await call_next(request)
        client_id = self._get_client_id(request)
        if await self._is_rate_limited(client_id, request):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.rate_limit_per_minute} requests per minute allowed",
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.rate_limit_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60),
                },
            )
        response = await call_next(request)
        remaining = await self._get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        return response

    def _should_skip_rate_limit(self, request: Request) -> bool:
        """
        Check if request should skip rate limiting
        """
        skip_paths = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
        return any((request.url.path.startswith(path) for path in skip_paths))

    def _get_client_id(self, request: Request) -> str:
        """
        Get client identifier for rate limiting
        """
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address considering proxies
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    async def _is_rate_limited(self, client_id: str, request: Request) -> bool:
        """
        Check if client is rate limited using sliding window
        """
        redis_client = get_redis()
        if not redis_client:
            logger.warning("Redis not available for rate limiting")
            return False
        try:
            current_time = int(time.time())
            window_start = current_time - 60
            key = f"rate_limit:{client_id}"
            await redis_client.zremrangebyscore(key, 0, window_start)
            current_count = await redis_client.zcard(key)
            if current_count >= self.rate_limit_per_minute:
                return True
            await redis_client.zadd(key, {str(current_time): current_time})
            await redis_client.expire(key, 120)
            return False
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False

    async def _get_remaining_requests(self, client_id: str) -> int:
        """
        Get remaining requests for client
        """
        redis_client = get_redis()
        if not redis_client:
            return self.rate_limit_per_minute
        try:
            current_time = int(time.time())
            window_start = current_time - 60
            key = f"rate_limit:{client_id}"
            await redis_client.zremrangebyscore(key, 0, window_start)
            current_count = await redis_client.zcard(key)
            return max(0, self.rate_limit_per_minute - current_count)
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return self.rate_limit_per_minute
