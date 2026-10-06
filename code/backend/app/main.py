"""
Main FastAPI application with production-ready configuration
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

import uvicorn
from app.api.v1.router import api_router
from config.database import close_database, init_database
from config.settings import settings
from exceptions.base_exceptions import (
    AuthenticationException,
    AuthorizationException,
    BaseChainFinityException,
    ConflictException,
    ErrorCategory,
    InsufficientResourcesException,
    RateLimitException,
    ResourceNotFoundException,
    ValidationException,
)
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from middleware.auth_middleware import AuthMiddleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
from middleware.security_middleware import SecurityMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.monitoring.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager
    """
    # Startup
    logger.info("Starting ChainFinity API...")
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    try:
        from services.ai import get_ai_service

        ai_load = await get_ai_service().startup()
        if ai_load:
            logger.info(f"AI models: {ai_load}")
    except Exception as e:
        logger.error(f"AI model startup failed (continuing with fallbacks): {e}")

    yield

    try:
        from services.ai import get_ai_service

        await get_ai_service().shutdown()
    except Exception as e:
        logger.error(f"Error shutting down AI service: {e}")

    # Shutdown
    logger.info("Shutting down ChainFinity API...")
    try:
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app.APP_NAME,
    description=settings.app.APP_DESCRIPTION,
    version=settings.app.APP_VERSION,
    docs_url=(
        settings.app.DOCS_URL if not settings.app.ENVIRONMENT == "production" else None
    ),
    redoc_url=(
        settings.app.REDOC_URL if not settings.app.ENVIRONMENT == "production" else None
    ),
    openapi_url=(
        "/openapi.json" if not settings.app.ENVIRONMENT == "production" else None
    ),
    lifespan=lifespan,
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add CORS middleware
# Browsers reject `Access-Control-Allow-Origin: *` when credentials are
# allowed, so a wildcard origin and allow_credentials=True cannot be combined.
# When origins is the wildcard, fall back to a regex that echoes any origin
# (which IS permitted with credentials) instead of the literal "*".
_cors_origins = settings.security.CORS_ORIGINS
_cors_allow_credentials = settings.security.CORS_ALLOW_CREDENTIALS
_cors_kwargs = dict(
    allow_credentials=_cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
if _cors_origins == ["*"] and _cors_allow_credentials:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        **_cors_kwargs,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        **_cors_kwargs,
    )

# Add trusted host middleware for production
if settings.app.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.security.ALLOWED_HOSTS,
    )

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Add logging middleware
app.add_middleware(LoggingMiddleware)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation error",
            "details": errors,
            "code": "VALIDATION_ERROR",
        },
    )


def _status_for_domain_exception(exc: BaseChainFinityException) -> int:
    explicit = getattr(exc, "http_status", None)
    if isinstance(explicit, int):
        return explicit
    """Map structured domain exceptions to HTTP status codes.

    Previously these exceptions fell through to the generic Exception handler
    and every business error (not found, validation, limits, ...) surfaced as
    an opaque 500.
    """
    if isinstance(exc, ResourceNotFoundException):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, AuthenticationException):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, AuthorizationException):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, ConflictException):
        return status.HTTP_409_CONFLICT
    if isinstance(exc, RateLimitException):
        return status.HTTP_429_TOO_MANY_REQUESTS
    if isinstance(exc, (ValidationException, InsufficientResourcesException)):
        return status.HTTP_400_BAD_REQUEST
    category_map = {
        ErrorCategory.VALIDATION: status.HTTP_400_BAD_REQUEST,
        ErrorCategory.AUTHENTICATION: status.HTTP_401_UNAUTHORIZED,
        ErrorCategory.AUTHORIZATION: status.HTTP_403_FORBIDDEN,
        ErrorCategory.BUSINESS_LOGIC: status.HTTP_400_BAD_REQUEST,
        ErrorCategory.COMPLIANCE: status.HTTP_403_FORBIDDEN,
    }
    return category_map.get(exc.category, status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.exception_handler(BaseChainFinityException)
async def chainfinity_exception_handler(
    request: Request, exc: BaseChainFinityException
):
    """Translate structured domain exceptions into HTTP responses"""
    status_code = _status_for_domain_exception(exc)
    if status_code >= 500:
        logger.error(f"Domain exception: {exc}", exc_info=True)
    else:
        logger.info(f"Domain exception: {exc}")
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.user_message,
            "code": exc.error_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if settings.app.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(exc),
                "code": "INTERNAL_SERVER_ERROR",
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )


# Application start time for uptime calculation
import time as _time

_app_start_time = _time.time()


# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint"""
    from config.database import check_database_health, check_redis_health

    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()

    services = {
        "database": "healthy" if db_healthy else "unhealthy",
        "redis": "healthy" if redis_healthy else "unhealthy",
    }

    overall_status = (
        "healthy" if all(s == "healthy" for s in services.values()) else "unhealthy"
    )

    from services.ai import get_ai_service

    ai_status = get_ai_service().status()
    ai_info = {
        "enabled": ai_status["enabled"],
        "package_available": ai_status["package_available"],
        "trained_models": [
            name
            for name, info in ai_status["models"].items()
            if info["loaded"] and info["mode"] == "trained"
        ],
    }

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app.APP_VERSION,
        "services": services,
        "ai": ai_info,
        "uptime_seconds": int(_time.time() - _app_start_time),
    }


# Root endpoint
@app.get("/", tags=["system"])
async def root() -> dict:
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app.APP_NAME}",
        "version": settings.app.APP_VERSION,
        "environment": settings.app.ENVIRONMENT,
        "docs_url": (
            settings.app.DOCS_URL
            if not settings.app.ENVIRONMENT == "production"
            else None
        ),
    }


# Include API router
app.include_router(api_router, prefix=settings.app.API_V1_PREFIX)


# Run application
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        workers=settings.app.WORKERS if settings.app.ENVIRONMENT == "production" else 1,
        reload=settings.app.DEBUG,
        log_level=settings.monitoring.LOG_LEVEL.lower(),
    )
