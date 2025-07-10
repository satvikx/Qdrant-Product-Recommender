import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    # Database settings
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "products")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")

    # Qdrant settings
    QDRANT_URL: str = os.getenv("QDRANT_URL", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "products_new")

    # Embedding settings
    MODEL_NAME: str = os.getenv("MODEL_NAME", "BAAI/bge-small-en-v1.5")

    # Admin settings
    ADMIN_BEARER_TOKEN: str = os.getenv("ADMIN_BEARER_TOKEN", "your-secure-admin-token")

    # Sync settings
    DEFAULT_BATCH_SIZE: int = int(os.getenv("DEFAULT_BATCH_SIZE", "100"))
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", "1000"))

    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"


settings = Settings()
