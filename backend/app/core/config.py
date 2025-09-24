import os
from enum import Enum

from pydantic import BaseSettings


class DeploymentType(Enum):
    """Supported deployment types."""

    ONPREMISE = "onpremise"
    CLOUD = "cloud"
    EDGE = "edge"


class DatabaseType(Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    SUPABASE = "supabase"


class StorageType(Enum):
    """Supported storage types."""

    LOCAL = "local"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class AuthType(Enum):
    """Supported authentication types."""

    LOCAL = "local"
    OAUTH = "oauth"
    SAML = "saml"
    LDAP = "ldap"


class BaseConfig(BaseSettings):
    """Base configuration class."""

    class Config:
        env_file = ".env"
        case_sensitive = True


class OnPremiseSettings(BaseConfig):
    """Configuration for on-premise deployment."""

    # Deployment
    DEPLOYMENT_TYPE: DeploymentType = DeploymentType.ONPREMISE

    # Database
    DATABASE_TYPE: DatabaseType = DatabaseType.POSTGRESQL
    DATABASE_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/marmot_industrial"
    )

    # Storage
    STORAGE_TYPE: StorageType = StorageType.LOCAL
    STORAGE_PATH: str = "./storage"

    # Authentication
    AUTH_TYPE: AuthType = AuthType.LOCAL

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: list = ["localhost", "127.0.0.1", "0.0.0.0"]

    # Performance
    MAX_WORKERS: int = 4
    MAX_CONNECTIONS: int = 100

    # Video Processing
    VIDEO_PROCESSING_THREADS: int = 2
    MAX_VIDEO_STREAMS: int = 8

    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS_PER_IP: int = 10
    WEBSOCKET_PING_INTERVAL: int = 30

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # Development
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"


class CloudSettings(BaseConfig):
    """Configuration for cloud deployment."""

    # Deployment
    DEPLOYMENT_TYPE: DeploymentType = DeploymentType.CLOUD

    # Database
    DATABASE_TYPE: DatabaseType = DatabaseType.SUPABASE
    DATABASE_URL: str = ""  # Should be provided via environment

    # Storage
    STORAGE_TYPE: StorageType = StorageType.S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = "us-east-1"

    # Authentication
    AUTH_TYPE: AuthType = AuthType.OAUTH
    OAUTH_CLIENT_ID: str = ""
    OAUTH_CLIENT_SECRET: str = ""

    # Security
    SECRET_KEY: str = ""  # Should be provided via environment
    ALLOWED_HOSTS: list = ["*"]  # Configure properly for production

    # Performance (adjusted for cloud)
    MAX_WORKERS: int = 8
    MAX_CONNECTIONS: int = 1000

    # Video Processing (cloud optimized)
    VIDEO_PROCESSING_THREADS: int = 4
    MAX_VIDEO_STREAMS: int = 50

    # WebSocket (higher limits for cloud)
    WEBSOCKET_MAX_CONNECTIONS_PER_IP: int = 50
    WEBSOCKET_PING_INTERVAL: int = 60

    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090

    # Development
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class EdgeSettings(BaseConfig):
    """Configuration for edge device deployment."""

    # Deployment
    DEPLOYMENT_TYPE: DeploymentType = DeploymentType.EDGE

    # Database (lightweight for edge)
    DATABASE_TYPE: DatabaseType = DatabaseType.SQLITE
    DATABASE_URL: str = "sqlite:///./edge_marmot.db"

    # Storage
    STORAGE_TYPE: StorageType = StorageType.LOCAL
    STORAGE_PATH: str = "/var/lib/marmot"

    # Authentication
    AUTH_TYPE: AuthType = AuthType.LOCAL

    # Security
    SECRET_KEY: str = "edge-device-key"  # Should be unique per device
    ALLOWED_HOSTS: list = ["localhost", "*.local"]

    # Performance (optimized for edge devices)
    MAX_WORKERS: int = 2
    MAX_CONNECTIONS: int = 20

    # Video Processing (limited for edge)
    VIDEO_PROCESSING_THREADS: int = 1
    MAX_VIDEO_STREAMS: int = 4

    # WebSocket (limited for edge)
    WEBSOCKET_MAX_CONNECTIONS_PER_IP: int = 5
    WEBSOCKET_PING_INTERVAL: int = 20

    # Monitoring (minimal for edge)
    ENABLE_METRICS: bool = False

    # Development
    DEBUG: bool = False
    LOG_LEVEL: str = "ERROR"

    # Edge-specific
    SYNC_INTERVAL: int = 300  # Sync with central server every 5 minutes
    CENTRAL_SERVER_URL: str = ""  # URL of central management server


class Settings:
    """Settings factory based on deployment type."""

    @staticmethod
    def get_settings() -> BaseConfig:
        """Get configuration based on deployment type."""
        deployment_type = os.getenv("DEPLOYMENT_TYPE", "onpremise").lower()

        if deployment_type == "cloud":
            return CloudSettings()
        elif deployment_type == "edge":
            return EdgeSettings()
        else:
            return OnPremiseSettings()


# Global settings instance
settings = Settings.get_settings()


def get_settings() -> BaseConfig:
    """Get the current settings instance."""
    return settings


# Convenience functions for common config access
def get_database_url() -> str:
    """Get database URL."""
    return settings.DATABASE_URL


def get_deployment_type() -> DeploymentType:
    """Get deployment type."""
    return settings.DEPLOYMENT_TYPE


def is_development() -> bool:
    """Check if running in development mode."""
    return getattr(settings, "DEBUG", False)


def is_production() -> bool:
    """Check if running in production mode."""
    return not is_development()


def get_max_video_streams() -> int:
    """Get maximum number of video streams."""
    return getattr(settings, "MAX_VIDEO_STREAMS", 8)
