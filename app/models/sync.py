from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncRequest(BaseModel):
    batch_size: int = Field(default=100, ge=1, le=1000)
    force_reindex: bool = Field(
        default=False, description="Force re-indexing of already indexed products"
    )


class SyncResponse(BaseModel):
    success: bool
    message: str
    sync_id: str
    status: SyncStatus
    total_products: int
    processed_products: int
    failed_products: int
    batch_size: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    errors: List[str] = []


class SyncStatusResponse(BaseModel):
    last_sync: Optional[dict] = None
    collection_info: dict
    database_status: bool
    qdrant_status: bool


class ConnectionTestResponse(BaseModel):
    postgres_status: bool
    qdrant_status: bool
    postgres_message: str
    qdrant_message: str
