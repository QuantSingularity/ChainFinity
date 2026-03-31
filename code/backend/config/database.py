"""
Database configuration and connection management
Production-ready database setup with connection pooling, read replicas, and monitoring
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as redis
from config.settings import settings
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)
Base = declarative_base()
async_engine = create_async_engine(
    settings.database.DATABASE_URL,
    echo=settings.database.DB_ECHO,
    echo_pool=settings.database.DB_ECHO_POOL,
    poolclass=NullPool,  # Use NullPool for async
    future=True,
)
async_read_engine = None
if settings.database.DATABASE_READ_URL:
    async_read_engine = create_async_engine(
        settings.database.DATABASE_READ_URL,
        echo=settings.database.DB_ECHO,
        echo_pool=settings.database.DB_ECHO_POOL,
        poolclass=NullPool,  # Use NullPool for async
        future=True,
    )
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)
AsyncReadSessionLocal = None
if async_read_engine:
    AsyncReadSessionLocal = async_sessionmaker(
        bind=async_read_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
sync_engine = create_engine(
    settings.database.DATABASE_URL.replace("+asyncpg", ""),
    echo=settings.database.DB_ECHO,
    pool_size=settings.database.DB_POOL_SIZE,
    max_overflow=settings.database.DB_MAX_OVERFLOW,
    pool_timeout=settings.database.DB_POOL_TIMEOUT,
    pool_recycle=settings.database.DB_POOL_RECYCLE,
)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.from_url(
            settings.redis.REDIS_URL,
            password=settings.redis.REDIS_PASSWORD,
            db=settings.redis.REDIS_DB,
            max_connections=settings.redis.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.redis.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.redis.REDIS_SOCKET_CONNECT_TIMEOUT,
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None


async def close_redis() -> None:
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client instance"""
    return redis_client


@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> Any:
    """Set database connection parameters"""
    if "postgresql" in str(dbapi_connection):
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC'")
            cursor.execute("SET statement_timeout = '30s'")


@event.listens_for(async_engine.sync_engine, "checkout")
def receive_checkout(
    dbapi_connection: Any, connection_record: Any, connection_proxy: Any
) -> Any:
    """Log database connection checkout"""
    logger.debug("Database connection checked out")


@event.listens_for(async_engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection: Any, connection_record: Any) -> Any:
    """Log database connection checkin"""
    logger.debug("Database connection checked in")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_read_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get async read-only database session
    Uses read replica if available, otherwise falls back to primary
    """
    session_maker = (
        AsyncReadSessionLocal if AsyncReadSessionLocal else AsyncSessionLocal
    )
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session() -> Session:
    """
    Get synchronous database session for migrations and admin tasks
    """
    return SyncSessionLocal()


@asynccontextmanager
async def get_async_session_context():
    """
    Context manager for async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    """
    Check database connectivity and health
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_redis_health() -> bool:
    """
    Check Redis connectivity and health
    """
    try:
        if redis_client:
            await redis_client.ping()
            return True
        return False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


async def init_database() -> None:
    """
    Initialize database connections and create tables
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("Primary database connection established")
        if AsyncReadSessionLocal:
            async with AsyncReadSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            logger.info("Read replica database connection established")
        await init_redis()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_database() -> None:
    """
    Close all database connections
    """
    try:
        await async_engine.dispose()
        if async_read_engine:
            await async_read_engine.dispose()
        await close_redis()
        logger.info("All database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


class CacheManager:
    """Redis cache manager with TTL support"""

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """Get value from cache"""
        if redis_client:
            try:
                return await redis_client.get(key)
            except Exception as e:
                logger.error(f"Cache get error: {e}")
        return None

    @staticmethod
    async def set(key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if redis_client:
            try:
                ttl = ttl or settings.redis.CACHE_TTL
                await redis_client.setex(key, ttl, value)
                return True
            except Exception as e:
                logger.error(f"Cache set error: {e}")
        return False

    @staticmethod
    async def delete(key: str) -> bool:
        """Delete value from cache"""
        if redis_client:
            try:
                await redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"Cache delete error: {e}")
        return False

    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists in cache"""
        if redis_client:
            try:
                return await redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Cache exists error: {e}")
        return False


cache = CacheManager()


class DatabaseManager:
    """
    Database manager for handling complex transactions and operations
    """

    @staticmethod
    @asynccontextmanager
    async def transaction():
        """
        Context manager for database transactions with automatic rollback
        """
        async with AsyncSessionLocal() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise

    @staticmethod
    async def execute_raw_sql(sql: str, params: dict = None):
        """
        Execute raw SQL with parameters
        """
        async with AsyncSessionLocal() as session:
            result = await session.execute(sql, params or {})
            await session.commit()
            return result

    @staticmethod
    async def get_database_stats() -> dict:
        """
        Get database connection pool statistics
        """
        pool = async_engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }

    @staticmethod
    async def get_redis_stats() -> dict:
        """
        Get Redis connection statistics
        """
        try:
            if redis_client:
                info = await redis_client.info()
                return {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
        return {}

    @staticmethod
    async def health_check() -> dict:
        """
        Comprehensive health check for database and Redis
        """
        db_healthy = await check_database_health()
        redis_healthy = await check_redis_health()
        db_stats = await DatabaseManager.get_database_stats()
        redis_stats = await DatabaseManager.get_redis_stats()
        return {
            "database": {"healthy": db_healthy, "stats": db_stats},
            "redis": {"healthy": redis_healthy, "stats": redis_stats},
            "overall_healthy": db_healthy and redis_healthy,
        }


db_manager = DatabaseManager()
