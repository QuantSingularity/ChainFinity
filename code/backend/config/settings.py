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
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"])
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
    CORS_ORIGINS: List[str] = Field(default=["*"])
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
    # RPC request timeout, in seconds. Applies to every call the backend
    # makes to ETH_RPC_URL (see services/blockchain/client.py). Kept
    # short so a misconfigured/unreachable node degrades an API response
    # in ~5s instead of hanging the request.
    WEB3_REQUEST_TIMEOUT: int = Field(default=5)

    # ChainFinity protocol contract addresses on ETH_RPC_URL / ETH_CHAIN_ID.
    # For local development these are picked up automatically from
    # code/blockchain/deployments/contracts.<network>.json (see
    # BLOCKCHAIN_DEPLOYMENT_FILE below and Web3Client._load_deployment) after
    # running `npm run deploy:localhost` in code/blockchain - you don't need
    # to copy addresses here by hand. Set these explicitly for staging/
    # production, where they take priority over the deployment file.
    GOVERNANCE_TOKEN_ADDRESS: Optional[str] = None
    ASSET_VAULT_ADDRESS: Optional[str] = None
    CROSS_CHAIN_MANAGER_ADDRESS: Optional[str] = None
    DEFI_PROTOCOL_ADDRESS: Optional[str] = None
    GOVERNANCE_ADDRESS: Optional[str] = None

    # Path to the JSON manifest scripts/deploy.js writes (address + ABI per
    # contract). Relative paths are resolved against the backend package
    # root (see services/blockchain/client.py:_BACKEND_ROOT), not the
    # process's current working directory. Defaults to the localhost
    # deployment produced by the blockchain workspace's own dev workflow
    # (see code/blockchain/README and scripts/run_chainfinity.sh) so a
    # fresh local checkout works with zero configuration once contracts are
    # deployed.
    BLOCKCHAIN_DEPLOYMENT_FILE: str = Field(
        default="../blockchain/deployments/contracts.localhost.json"
    )
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

    # Portfolio Configuration
    MAX_PORTFOLIOS_PER_USER: int = Field(default=10)
    REBALANCING_THRESHOLD: float = Field(default=5.0)
    MIN_TRADE_VALUE: float = Field(default=10.0)
    MAX_TRADE_VALUE: float = Field(default=1000000.0)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["*"]

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def validate_secret_key(cls, v: str, info: Any) -> str:
        insecure_default = "dev-secret-key-change-in-production"
        # We cannot access other fields via info.data reliably at this stage for
        # all Pydantic versions, so we read ENVIRONMENT directly from the raw
        # values that have already been validated (they are available in info.data
        # once the field order in the class body is respected).
        env = (info.data or {}).get("ENVIRONMENT", "development")
        if env == "production" and v == insecure_default:
            raise ValueError(
                "SECRET_KEY must be changed from the default value in production. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(64))"'
            )
        if len(v) < 32 and env == "production":
            raise ValueError(
                "SECRET_KEY must be at least 32 characters long in production."
            )
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["localhost", "127.0.0.1"]

    # Convenience property accessors for backward compatibility
    @property
    def app(self) -> Any:
        """Application settings accessor"""

        class AppSettings:
            def __init__(self, settings: Settings) -> None:
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
    def database(self) -> Any:
        """Database settings accessor"""

        class DatabaseSettings:
            def __init__(self, settings: Settings) -> None:
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
    def redis(self) -> Any:
        """Redis settings accessor"""

        class RedisSettings:
            def __init__(self, settings: Settings) -> None:
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
    def security(self) -> Any:
        """Security settings accessor"""

        class SecuritySettings:
            def __init__(self, settings: "Settings") -> None:
                self.SECRET_KEY = settings.SECRET_KEY
                self.JWT_ALGORITHM = settings.JWT_ALGORITHM
                self.ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
                self.REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
                self.RATE_LIMIT_PER_MINUTE = settings.RATE_LIMIT_PER_MINUTE
                self.RATE_LIMIT_BURST = settings.RATE_LIMIT_BURST
                self.CORS_ORIGINS = settings.CORS_ORIGINS
                self.CORS_ALLOW_CREDENTIALS = settings.CORS_ALLOW_CREDENTIALS
                self.ALLOWED_HOSTS = settings.ALLOWED_HOSTS
                # Password policy (previously missing here, which made
                # UserService._validate_password_strength raise AttributeError)
                self.PASSWORD_MIN_LENGTH = settings.PASSWORD_MIN_LENGTH
                self.PASSWORD_REQUIRE_UPPERCASE = settings.PASSWORD_REQUIRE_UPPERCASE
                self.PASSWORD_REQUIRE_LOWERCASE = settings.PASSWORD_REQUIRE_LOWERCASE
                self.PASSWORD_REQUIRE_NUMBERS = settings.PASSWORD_REQUIRE_NUMBERS
                self.PASSWORD_REQUIRE_SPECIAL = settings.PASSWORD_REQUIRE_SPECIAL
                self.API_KEY_HEADER = settings.API_KEY_HEADER
                self.ENCRYPTION_KEY = settings.ENCRYPTION_KEY
                self.FIELD_ENCRYPTION_ENABLED = settings.FIELD_ENCRYPTION_ENABLED

        return SecuritySettings(self)

    @property
    def blockchain(self) -> Any:
        """Blockchain settings accessor"""

        class BlockchainSettings:
            def __init__(self, settings: Settings) -> None:
                self.ETH_RPC_URL = settings.ETH_RPC_URL
                self.ETH_WEBSOCKET_URL = settings.ETH_WEBSOCKET_URL
                self.ETH_CHAIN_ID = settings.ETH_CHAIN_ID
                self.POLYGON_RPC_URL = settings.POLYGON_RPC_URL
                self.POLYGON_CHAIN_ID = settings.POLYGON_CHAIN_ID
                self.BSC_RPC_URL = settings.BSC_RPC_URL
                self.BSC_CHAIN_ID = settings.BSC_CHAIN_ID
                self.GAS_PRICE_STRATEGY = settings.GAS_PRICE_STRATEGY
                self.MAX_GAS_PRICE = settings.MAX_GAS_PRICE
                self.WEB3_REQUEST_TIMEOUT = settings.WEB3_REQUEST_TIMEOUT
                self.GOVERNANCE_TOKEN_ADDRESS = settings.GOVERNANCE_TOKEN_ADDRESS
                self.ASSET_VAULT_ADDRESS = settings.ASSET_VAULT_ADDRESS
                self.CROSS_CHAIN_MANAGER_ADDRESS = settings.CROSS_CHAIN_MANAGER_ADDRESS
                self.DEFI_PROTOCOL_ADDRESS = settings.DEFI_PROTOCOL_ADDRESS
                self.GOVERNANCE_ADDRESS = settings.GOVERNANCE_ADDRESS
                self.BLOCKCHAIN_DEPLOYMENT_FILE = settings.BLOCKCHAIN_DEPLOYMENT_FILE
                self.ETHERSCAN_API_KEY = settings.ETHERSCAN_API_KEY
                self.POLYGONSCAN_API_KEY = settings.POLYGONSCAN_API_KEY

        return BlockchainSettings(self)

    @property
    def compliance(self) -> Any:
        """Compliance settings accessor"""

        class ComplianceSettings:
            def __init__(self, settings: Settings) -> None:
                self.KYC_ENABLED = settings.KYC_ENABLED
                self.KYC_PROVIDER = settings.KYC_PROVIDER
                self.KYC_API_KEY = settings.KYC_API_KEY
                self.KYC_API_SECRET = settings.KYC_API_SECRET
                self.AML_ENABLED = settings.AML_ENABLED
                self.AML_PROVIDER = settings.AML_PROVIDER
                self.AML_API_KEY = settings.AML_API_KEY
                self.TRANSACTION_MONITORING_ENABLED = (
                    settings.TRANSACTION_MONITORING_ENABLED
                )
                self.SUSPICIOUS_AMOUNT_THRESHOLD = settings.SUSPICIOUS_AMOUNT_THRESHOLD
                self.DAILY_TRANSACTION_LIMIT = settings.DAILY_TRANSACTION_LIMIT
                self.REGULATORY_REPORTING_ENABLED = (
                    settings.REGULATORY_REPORTING_ENABLED
                )
                self.AUDIT_LOG_RETENTION_DAYS = settings.AUDIT_LOG_RETENTION_DAYS

        return ComplianceSettings(self)

    @property
    def monitoring(self) -> Any:
        """Monitoring settings accessor"""

        class MonitoringSettings:
            def __init__(self, settings: Settings) -> None:
                self.LOG_LEVEL = settings.LOG_LEVEL
                self.LOG_FORMAT = settings.LOG_FORMAT
                self.LOG_FILE = settings.LOG_FILE
                self.METRICS_ENABLED = settings.METRICS_ENABLED
                self.METRICS_PORT = settings.METRICS_PORT
                self.HEALTH_CHECK_INTERVAL = settings.HEALTH_CHECK_INTERVAL
                self.SENTRY_DSN = settings.SENTRY_DSN
                self.SENTRY_ENVIRONMENT = settings.SENTRY_ENVIRONMENT

        return MonitoringSettings(self)

    @property
    def external_apis(self) -> Any:
        """External APIs settings accessor"""

        class ExternalAPISettings:
            def __init__(self, settings: Settings) -> None:
                self.COINMARKETCAP_API_KEY = settings.COINMARKETCAP_API_KEY
                self.CRYPTOCOMPARE_API_KEY = settings.CRYPTOCOMPARE_API_KEY
                self.ALPHA_VANTAGE_API_KEY = settings.ALPHA_VANTAGE_API_KEY

        return ExternalAPISettings(self)

    @property
    def portfolio(self) -> Any:
        """Portfolio settings accessor"""

        class PortfolioSettings:
            def __init__(self, settings: Settings) -> None:
                self.MAX_PORTFOLIOS_PER_USER = settings.MAX_PORTFOLIOS_PER_USER
                self.REBALANCING_THRESHOLD = settings.REBALANCING_THRESHOLD
                self.MIN_TRADE_VALUE = settings.MIN_TRADE_VALUE
                self.MAX_TRADE_VALUE = settings.MAX_TRADE_VALUE

        return PortfolioSettings(self)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
