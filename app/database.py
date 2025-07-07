# Database connections (PostgreSQL, Qdrant client setup)
import asyncpg
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def create_pool(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.postgres_url, min_size=5, max_size=10, command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def close_pool(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection from pool"""
        if not self.pool:
            await self.create_pool()

        async with self.pool.acquire() as connection:
            yield connection

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()
