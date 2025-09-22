import os
from enum import Enum
from functools import lru_cache
from typing import Type

from app.core.database_service import DatabaseService


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    # Future: SUPABASE = "supabase"
    # Future: MONGODB = "mongodb"


class DatabaseFactory:
    """Factory for creating database service instances."""

    _instances = {}

    @classmethod
    def create_database_service(
        cls,
        database_type: DatabaseType = None
    ) -> DatabaseService:
        """Create a database service instance based on configuration."""

        if database_type is None:
            database_type = cls._get_database_type_from_env()

        if database_type in cls._instances:
            return cls._instances[database_type]

        if database_type == DatabaseType.POSTGRESQL:
            from app.core.postgresql_service import PostgreSQLService
            service = PostgreSQLService()
        elif database_type == DatabaseType.SQLITE:
            from app.core.postgresql_service import PostgreSQLService
            service = PostgreSQLService()
        else:
            raise ValueError(f"Unsupported database type: {database_type}")

        cls._instances[database_type] = service
        return service

    @classmethod
    def _get_database_type_from_env(cls) -> DatabaseType:
        """Determine database type from environment variables."""
        database_url = os.getenv("DATABASE_URL", "sqlite:///./marmot_industrial.db")
        database_type = os.getenv("DATABASE_TYPE", "").lower()

        if database_type == "postgresql":
            return DatabaseType.POSTGRESQL
        elif database_type == "sqlite":
            return DatabaseType.SQLITE

        if database_url.startswith("postgresql"):
            return DatabaseType.POSTGRESQL
        elif database_url.startswith("sqlite"):
            return DatabaseType.SQLITE
        else:
            return DatabaseType.POSTGRESQL

    @classmethod
    def clear_instances(cls):
        """Clear cached instances (useful for testing)."""
        cls._instances.clear()


@lru_cache(maxsize=1)
def get_database_service() -> DatabaseService:
    """Get the singleton database service instance."""
    return DatabaseFactory.create_database_service()


def get_db_service() -> DatabaseService:
    """Dependency injection function for FastAPI."""
    return get_database_service()