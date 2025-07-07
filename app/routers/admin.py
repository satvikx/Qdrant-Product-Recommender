from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import logging
from app.utils.auth import verify_admin_token
from app.services.sync_service import SyncService
from app.services.embedding_service import EmbeddingService
from app.database import db_manager
from app.models.sync import (
    SyncRequest,
    SyncResponse,
    SyncStatusResponse,
    ConnectionTestResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/sync", response_model=SyncResponse)
async def sync_products(request: SyncRequest, _: str = Depends(verify_admin_token)):
    """
    Main sync endpoint to fetch products from PostgreSQL and upload embeddings to Qdrant

    This endpoint:
    1. Fetches products where qdrant_indexed is FALSE
    2. Generates embeddings for these products
    3. Uploads embeddings to Qdrant vector database
    4. Updates qdrant_indexed to TRUE and sets qdrant_indexed_at timestamp
    """
    try:
        sync_service = SyncService()
        result = await sync_service.sync_products(
            batch_size=request.batch_size, force_reindex=request.force_reindex
        )
        return result

    except Exception as e:
        logger.error(f"Error in sync endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(_: str = Depends(verify_admin_token)):
    """
    Get sync status information

    Returns:
    - Last sync timestamp and details
    - Collection information
    - Database connection status
    """
    try:
        sync_service = SyncService()
        embedding_service = EmbeddingService()

        # Get last sync info
        last_sync = await sync_service.get_last_sync_info()

        # Get collection info
        collection_info = await embedding_service.get_collection_info()

        # Test connections
        db_status = await db_manager.test_connection()
        qdrant_status, _ = await embedding_service.test_connection()

        return SyncStatusResponse(
            last_sync=last_sync,
            collection_info=collection_info,
            database_status=db_status,
            qdrant_status=qdrant_status,
        )

    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/sync/test-connection", response_model=ConnectionTestResponse)
async def test_connections(_: str = Depends(verify_admin_token)):
    """
    Test both PostgreSQL and Qdrant connections

    Useful for debugging connectivity issues
    """
    try:
        # Test PostgreSQL connection
        postgres_status = await db_manager.test_connection()
        postgres_message = (
            "PostgreSQL connection successful"
            if postgres_status
            else "PostgreSQL connection failed"
        )

        # Test Qdrant connection
        embedding_service = EmbeddingService()
        qdrant_status, qdrant_message = await embedding_service.test_connection()

        return ConnectionTestResponse(
            postgres_status=postgres_status,
            qdrant_status=qdrant_status,
            postgres_message=postgres_message,
            qdrant_message=qdrant_message,
        )

    except Exception as e:
        logger.error(f"Error testing connections: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
