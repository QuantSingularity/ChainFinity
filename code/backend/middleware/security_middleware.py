"""
Security middleware for comprehensive request/response security
Implements security headers, request validation, and threat detection
"""

import ipaddress
import json
import logging
import time
from typing import Any, Callable, Optional

from config.database import cache
from config.settings import settings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS
from user_agents import parse

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware for production environments
    """

    def __init__(self, app: Any, **kwargs) -> None:
        super().__init__(app)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            "union select",
            "drop table",
            "insert into",
            "delete from",
            "<script",
            "javascript:",
            "eval(",
            "expression(",
            "vbscript:",
            "onload=",
            "onerror=",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through security checks
        """
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        security_check = await self.perform_security_checks(request, client_ip)
        if security_check:
            return security_check
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )
        response = self.add_security_headers(response)
        await self.log_security_metrics(request, response, client_ip, start_time)
        return response

    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request headers
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    async def perform_security_checks(
        self, request: Request, client_ip: str
    ) -> Optional[Response]:
        """
        Perform comprehensive security checks on incoming requests
        """
        if await self.is_ip_blocked(client_ip):
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN, content={"error": "Access denied"}
            )
        rate_limit_response = await self.check_rate_limit(request, client_ip)
        if rate_limit_response:
            return rate_limit_response
        if await self.detect_malicious_patterns(request):
            await self.flag_suspicious_activity(client_ip, "malicious_patterns")
            logger.warning(f"Malicious patterns detected from IP: {client_ip}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN, content={"error": "Request blocked"}
            )
        if not self.validate_user_agent(request):
            await self.flag_suspicious_activity(client_ip, "invalid_user_agent")
            logger.warning(f"Invalid user agent from IP: {client_ip}")
        if not await self.validate_request_size(request):
            logger.warning(f"Request too large from IP: {client_ip}")
            return JSONResponse(
                status_code=413, content={"error": "Request entity too large"}
            )
        return None

    async def is_ip_blocked(self, ip: str) -> bool:
        """
        Check if IP address is blocked
        """
        if ip in self.blocked_ips:
            return True
        blocked_key = f"blocked_ip:{ip}"
        is_blocked = await cache.exists(blocked_key)
        return is_blocked

    async def check_rate_limit(
        self, request: Request, client_ip: str
    ) -> Optional[Response]:
        """
        Check rate limiting for client IP
        """
        if request.url.path in ["/health", "/metrics"]:
            return None
        rate_key = f"rate_limit:{client_ip}"
        current_count = await cache.get(rate_key)
        if current_count is None:
            await cache.set(rate_key, "1", ttl=60)
            return None
        count = int(current_count)
        if count >= settings.security.RATE_LIMIT_PER_MINUTE:
            burst_key = f"burst_limit:{client_ip}"
            burst_count = await cache.get(burst_key)
            if burst_count and int(burst_count) >= settings.security.RATE_LIMIT_BURST:
                await self.block_ip_temporarily(client_ip, 300)
                logger.warning(f"IP blocked for rate limit violation: {client_ip}")
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Rate limit exceeded", "retry_after": 300},
                    headers={"Retry-After": "300"},
                )
            else:
                if burst_count:
                    await cache.set(burst_key, str(int(burst_count) + 1), ttl=3600)
                else:
                    await cache.set(burst_key, "1", ttl=3600)
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={"error": "Rate limit exceeded", "retry_after": 60},
                    headers={"Retry-After": "60"},
                )
        await cache.set(rate_key, str(count + 1), ttl=60)
        return None

    async def detect_malicious_patterns(self, request: Request) -> bool:
        """
        Detect malicious patterns in request
        """
        path_lower = request.url.path.lower()
        for pattern in self.suspicious_patterns:
            if pattern in path_lower:
                return True
        query_string = str(request.url.query).lower()
        for pattern in self.suspicious_patterns:
            if pattern in query_string:
                return True
        for header_name, header_value in request.headers.items():
            header_lower = header_value.lower()
            for pattern in self.suspicious_patterns:
                if pattern in header_lower:
                    return True
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8", errors="ignore").lower()
                    for pattern in self.suspicious_patterns:
                        if pattern in body_str:
                            return True
            except Exception:
                pass
        return False

    def validate_user_agent(self, request: Request) -> bool:
        """
        Validate user agent string
        """
        user_agent = request.headers.get("User-Agent", "")
        if not user_agent or len(user_agent) < 10:
            return False
        try:
            parse(user_agent)
            suspicious_bots = [
                "sqlmap",
                "nikto",
                "nmap",
                "masscan",
                "zap",
                "burp",
                "w3af",
                "havij",
            ]
            ua_lower = user_agent.lower()
            for bot in suspicious_bots:
                if bot in ua_lower:
                    return False
            return True
        except Exception:
            return False

    async def validate_request_size(self, request: Request) -> bool:
        """
        Validate request size limits
        """
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                size = int(content_length)
                max_size = 10 * 1024 * 1024
                if request.url.path.startswith("/api/v1/upload"):
                    max_size = 100 * 1024 * 1024
                return size <= max_size
            except ValueError:
                return False
        return True

    async def flag_suspicious_activity(
        self, client_ip: str, activity_type: str
    ) -> None:
        """
        Flag suspicious activity for monitoring
        """
        suspicious_key = f"suspicious:{client_ip}:{activity_type}"
        count = await cache.get(suspicious_key)
        if count:
            new_count = int(count) + 1
        else:
            new_count = 1
        await cache.set(suspicious_key, str(new_count), ttl=3600)
        if new_count >= 5:
            await self.block_ip_temporarily(client_ip, 1800)
            logger.warning(f"IP blocked for suspicious activity: {client_ip}")

    async def block_ip_temporarily(self, ip: str, duration: int) -> None:
        """
        Block IP address temporarily
        """
        blocked_key = f"blocked_ip:{ip}"
        await cache.set(blocked_key, "1", ttl=duration)
        logger.warning(f"IP {ip} blocked for {duration} seconds")

    def add_security_headers(self, response: Response) -> Response:
        """
        Add security headers to response
        """
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';",
        }
        for header, value in security_headers.items():
            response.headers[header] = value
        if "Server" in response.headers:
            del response.headers["Server"]
        response.headers["X-Security-Framework"] = "ChainFinity-Security-v2.0"
        return response

    async def log_security_metrics(
        self, request: Request, response: Response, client_ip: str, start_time: float
    ) -> None:
        """
        Log security-related metrics
        """
        processing_time = time.time() - start_time
        security_log = {
            "timestamp": time.time(),
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "processing_time": processing_time,
            "user_agent": request.headers.get("User-Agent", ""),
            "referer": request.headers.get("Referer", ""),
            "content_length": request.headers.get("Content-Length", "0"),
        }
        if (
            response.status_code >= 400
            or processing_time > 5.0
            or request.url.path.startswith("/admin")
        ):
            logger.warning(f"Security event: {json.dumps(security_log)}")
        metrics_key = f"security_metrics:{int(time.time() // 60)}"
        await cache.set(metrics_key, json.dumps(security_log), ttl=3600)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP whitelist middleware for admin endpoints
    """

    def __init__(self, app: Any, whitelist_cidrs: list = None) -> None:
        super().__init__(app)
        self.whitelist_cidrs = whitelist_cidrs or []
        self.admin_paths = ["/admin", "/api/v1/admin"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check IP whitelist for admin endpoints
        """
        is_admin_path = any(
            (request.url.path.startswith(path) for path in self.admin_paths)
        )
        if is_admin_path and self.whitelist_cidrs:
            client_ip = self.get_client_ip(request)
            if not self.is_ip_whitelisted(client_ip):
                logger.warning(
                    f"Non-whitelisted IP attempted admin access: {client_ip}"
                )
                return JSONResponse(
                    status_code=HTTP_403_FORBIDDEN, content={"error": "Access denied"}
                )
        return await call_next(request)

    def get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    def is_ip_whitelisted(self, ip: str) -> bool:
        """
        Check if IP is in whitelist
        """
        try:
            client_ip = ipaddress.ip_address(ip)
            for cidr in self.whitelist_cidrs:
                network = ipaddress.ip_network(cidr, strict=False)
                if client_ip in network:
                    return True
            return False
        except ValueError:
            return False
