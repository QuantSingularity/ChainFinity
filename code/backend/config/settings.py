"""
ChainFinity Backend Configuration Settings
Production-ready configuration with environment-specific settings
"""

from functools import lru_cache
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main settings class with all configuration"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application Settings
    APP_NAME: str = Field(default="ChainFinity API")
    APP_VERSION: str = Field(default="2.0.0")
    APP_DESCRIPTION: str = Field(default="Production-ready DeFi Analytics Platform")
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)
    API_V1_PREFIX: str = Field(default="/api/v1")
    DOCS_URL: str = Field(default="/docs")
    REDOC_URL: str = Field(default="/redoc")
    NOTIFICATION_SERVICE_URL: Optional[str] = None
    ANALYTICS_SERVICE_URL: Optional[str] = None

    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/chainfinity"
    )
    DATABASE_READ_URL: Optional[str] = None
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=30)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_POOL_RECYCLE: int = Field(default=3600)
    DB_ECHO: bool = Field(default=False)
    DB_ECHO_POOL: bool = Field(default=False)

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = Field(default=0)
    REDIS_MAX_CONNECTIONS: int = Field(default=20)
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)
    CACHE_TTL: int = Field(default=3600)
    SESSION_TTL: int = Field(default=86400)

    # Security Configuration
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True)
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True)
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True)
    PASSWORD_REQUIRE_SPECIAL: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST: int = Field(default=100)
    API_KEY_HEADER: str = Field(default="X-API-Key")
    CORS_ORIGINS: str = Field(default="*")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    ENCRYPTION_KEY: Optional[str] = None
    FIELD_ENCRYPTION_ENABLED: bool = Field(default=True)

    # Blockchain Configuration
    ETH_RPC_URL: str = Field(default="https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
    ETH_WEBSOCKET_URL: Optional[str] = None
    ETH_CHAIN_ID: int = Field(default=1)
    POLYGON_RPC_URL: Optional[str] = None
    POLYGON_CHAIN_ID: int = Field(default=137)
    BSC_RPC_URL: Optional[str] = None
    BSC_CHAIN_ID: int = Field(default=56)
    GAS_PRICE_STRATEGY: str = Field(default="medium")
    MAX_GAS_PRICE: int = Field(default=100)
    GOVERNANCE_TOKEN_ADDRESS: Optional[str] = None
    ASSET_VAULT_ADDRESS: Optional[str] = None
    ETHERSCAN_API_KEY: Optional[str] = None
    POLYGONSCAN_API_KEY: Optional[str] = None

    # Compliance Configuration
    KYC_ENABLED: bool = Field(default=True)
    KYC_PROVIDER: str = Field(default="jumio")
    KYC_API_KEY: Optional[str] = None
    KYC_API_SECRET: Optional[str] = None
    AML_ENABLED: bool = Field(default=True)
    AML_PROVIDER: str = Field(default="chainalysis")
    AML_API_KEY: Optional[str] = None
    TRANSACTION_MONITORING_ENABLED: bool = Field(default=True)
    SUSPICIOUS_AMOUNT_THRESHOLD: float = Field(default=10000.0)
    DAILY_TRANSACTION_LIMIT: float = Field(default=50000.0)
    REGULATORY_REPORTING_ENABLED: bool = Field(default=True)
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=2555)

    # Monitoring Configuration
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")
    LOG_FILE: Optional[str] = None
    METRICS_ENABLED: bool = Field(default=True)
    METRICS_PORT: int = Field(default=8001)
    HEALTH_CHECK_INTERVAL: int = Field(default=30)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = Field(default="production")

    # External API Configuration
    COINMARKETCAP_API_KEY: Optional[str] = None
    CRYPTOCOMPARE_API_KEY: Optional[str] = None
    ALPHA_VANTAGE_API_KEY: Optional[str] = None

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Convenience property accessors for backward compatibility
    @property
    def app(self) -> "AppSettings":
        """Application settings accessor"""

        class AppSettings:
            def __init__(self, settings: "Settings") -> None:
                self.APP_NAME = settings.APP_NAME
                self.APP_VERSION = settings.APP_VERSION
                self.APP_DESCRIPTION = settings.APP_DESCRIPTION
                self.ENVIRONMENT = settings.ENVIRONMENT
                self.DEBUG = settings.DEBUG
                self.HOST = settings.HOST
                self.PORT = settings.PORT
                self.WORKERS = settings.WORKERS
                self.API_V1_PREFIX = settings.API_V1_PREFIX
                self.DOCS_URL = settings.DOCS_URL
                self.REDOC_URL = settings.REDOC_URL

        return AppSettings(self)

    @property
    def database(self) -> "DatabaseSettings":
        """Database settings accessor"""

        class DatabaseSettings:
            def __init__(self, settings: "Settings") -> None:
                self.DATABASE_URL = settings.DATABASE_URL
                self.DATABASE_READ_URL = settings.DATABASE_READ_URL
                self.DB_POOL_SIZE = settings.DB_POOL_SIZE
                self.DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW
                self.DB_POOL_TIMEOUT = settings.DB_POOL_TIMEOUT
                self.DB_POOL_RECYCLE = settings.DB_POOL_RECYCLE
                self.DB_ECHO = settings.DB_ECHO
                self.DB_ECHO_POOL = settings.DB_ECHO_POOL

        return DatabaseSettings(self)

    @property
    def redis(self) -> "RedisSettings":
        """Redis settings accessor"""

        class RedisSettings:
            def __init__(self, settings: "Settings") -> None:
                self.REDIS_URL = settings.REDIS_URL
                self.REDIS_PASSWORD = settings.REDIS_PASSWORD
                self.REDIS_DB = settings.REDIS_DB
                self.REDIS_MAX_CONNECTIONS = settings.REDIS_MAX_CONNECTIONS
                self.REDIS_SOCKET_TIMEOUT = settings.REDIS_SOCKET_TIMEOUT
                self.REDIS_SOCKET_CONNECT_TIMEOUT = (
                    settings.REDIS_SOCKET_CONNECT_TIMEOUT
                )
                self.CACHE_TTL = settings.CACHE_TTL
                self.SESSION_TTL = settings.SESSION_TTL

        return RedisSettings(self)

    @property
    def security(self) -> "SecuritySettings":
        """Security settings accessor"""

        class SecuritySettings:
            def __init__(self, settings: "Settings") -> None:
                self.SECRET_KEY = settings.SECRET_KEY
                self.ALGORITHM = settings.JWT_ALGORITHM
                self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
                self.REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
                self.RATE_LIMIT_PER_MINUTE = settings.RATE_LIMIT_PER_MINUTE
                self.RATE_LIMIT_BURST = settings.RATE_LIMIT_BURST
                self.CORS_ORIGINS = settings.CORS_ORIGINS
                self.CORS_ALLOW_CREDENTIALS = settings.CORS_ALLOW_CREDENTIALS

        return SecuritySettings(self)

    @property
    def blockchain(self) -> "BlockchainSettings":
        """Blockchain settings accessor"""

        class BlockchainSettings:
            def __init__(self, settings: "Settings") -> None:
                self.ETH_RPC_URL = settings.ETH_RPC_URL
                self.ETH_CHAIN_ID = settings.ETH_CHAIN_ID

        return BlockchainSettings(self)

    @property
    def compliance(self) -> "ComplianceSettings":
        """Compliance settings accessor"""

        class ComplianceSettings:
            def __init__(self, settings: "Settings") -> None:
                self.KYC_ENABLED = settings.KYC_ENABLED
                self.AML_ENABLED = settings.AML_ENABLED

        return ComplianceSettings(self)

    @property
    def monitoring(self) -> "MonitoringSettings":
        """Monitoring settings accessor"""

        class MonitoringSettings:
            def __init__(self, settings: "Settings") -> None:
                self.LOG_LEVEL = settings.LOG_LEVEL
                self.METRICS_ENABLED = settings.METRICS_ENABLED

        return MonitoringSettings(self)

    @property
    def external_apis(self) -> "ExternalAPISettings":
        """External APIs settings accessor"""

        class ExternalAPISettings:
            def __init__(self, settings: "Settings") -> None:
                self.COINMARKETCAP_API_KEY = settings.COINMARKETCAP_API_KEY
                self.CRYPTOCOMPARE_API_KEY = settings.CRYPTOCOMPARE_API_KEY
                self.ALPHA_VANTAGE_API_KEY = settings.ALPHA_VANTAGE_API_KEY

        return ExternalAPISettings(self)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
