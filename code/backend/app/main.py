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

    yield

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.CORS_ORIGINS,
    allow_credentials=settings.security.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if settings.app.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure with actual allowed hosts
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

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "version": settings.app.APP_VERSION,
        "services": services,
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
