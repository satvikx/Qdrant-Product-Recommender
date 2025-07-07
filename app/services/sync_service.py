import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
import logging
from app.database import db_manager
from app.services.embedding_service import EmbeddingService
from app.models.product import Product, ProductForEmbedding, ProductUpdate
from app.models.sync import SyncStatus, SyncResponse

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    async def sync_products(
        self, batch_size: int = 100, force_reindex: bool = False
    ) -> SyncResponse:
        """Main sync function"""
        sync_id = str(uuid.uuid4())
        started_at = datetime.now()

        logger.info(
            f"Starting sync {sync_id} with batch_size={batch_size}, force_reindex={force_reindex}"
        )

        try:
            # Ensure collection exists
            if not await self.embedding_service.ensure_collection_exists():
                return SyncResponse(
                    success=False,
                    message="Failed to ensure collection exists",
                    sync_id=sync_id,
                    status=SyncStatus.FAILED,
                    total_products=0,
                    processed_products=0,
                    failed_products=0,
                    batch_size=batch_size,
                    started_at=started_at,
                    errors=["Collection creation failed"],
                )

            # Get products to sync
            products_to_sync = await self.get_products_to_sync(force_reindex)
            total_products = len(products_to_sync)

            if total_products == 0:
                completed_at = datetime.now()
                return SyncResponse(
                    success=True,
                    message="No products to sync",
                    sync_id=sync_id,
                    status=SyncStatus.SUCCESS,
                    total_products=0,
                    processed_products=0,
                    failed_products=0,
                    batch_size=batch_size,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=(completed_at - started_at).total_seconds(),
                )

            # Process in batches
            processed_products = 0
            failed_products = 0
            errors = []

            for i in range(0, total_products, batch_size):
                batch = products_to_sync[i : i + batch_size]
                batch_products = [ProductForEmbedding(**product) for product in batch]

                try:
                    # Add to vector database
                    successful_ids, failed_ids = (
                        await self.embedding_service.add_products_to_vector_db(
                            batch_products
                        )
                    )

                    # Update database for successful products
                    if successful_ids:
                        await self.update_products_sync_status(successful_ids, True)
                        processed_products += len(successful_ids)

                    # Handle failed products
                    if failed_ids:
                        failed_products += len(failed_ids)
                        errors.extend(
                            [f"Failed to process product {pid}" for pid in failed_ids]
                        )
                        logger.error(
                            f"Failed to process {len(failed_ids)} products in batch"
                        )

                    logger.info(
                        f"Processed batch {i//batch_size + 1}: {len(successful_ids)} success, {len(failed_ids)} failed"
                    )

                except Exception as e:
                    # Mark entire batch as failed
                    batch_failed = len(batch)
                    failed_products += batch_failed
                    errors.append(f"Batch processing failed: {str(e)}")
                    logger.error(f"Batch processing failed: {e}")

            # Record sync completion
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            await self.record_sync_completion(
                sync_id,
                started_at,
                completed_at,
                total_products,
                processed_products,
                failed_products,
            )

            # Determine final status
            if failed_products == 0:
                status = SyncStatus.SUCCESS
                success = True
                message = f"Successfully synced {processed_products} products"
            elif processed_products > 0:
                status = SyncStatus.PARTIAL
                success = True
                message = f"Partially synced: {processed_products} success, {failed_products} failed"
            else:
                status = SyncStatus.FAILED
                success = False
                message = f"Sync failed: {failed_products} products failed"

            return SyncResponse(
                success=success,
                message=message,
                sync_id=sync_id,
                status=status,
                total_products=total_products,
                processed_products=processed_products,
                failed_products=failed_products,
                batch_size=batch_size,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                errors=errors[:10],  # Limit errors in response
            )

        except Exception as e:
            logger.error(f"Sync {sync_id} failed with error: {e}")
            completed_at = datetime.now()
            return SyncResponse(
                success=False,
                message=f"Sync failed: {str(e)}",
                sync_id=sync_id,
                status=SyncStatus.FAILED,
                total_products=0,
                processed_products=0,
                failed_products=0,
                batch_size=batch_size,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=(completed_at - started_at).total_seconds(),
                errors=[str(e)],
            )

    async def get_products_to_sync(self, force_reindex: bool = False) -> List[dict]:
        """Get products that need to be synced"""
        try:
            async with db_manager.get_connection() as conn:
                if force_reindex:
                    query = """
                    SELECT product_id, name, category, description, brand, type,
                           qdrant_indexed, qdrant_indexed_at
                    FROM products_new
                    ORDER BY product_id
                    """
                else:
                    query = """
                    SELECT product_id, name, category, description, brand, type,
                           qdrant_indexed, qdrant_indexed_at
                    FROM products_new
                    WHERE qdrant_indexed = FALSE OR qdrant_indexed IS NULL
                    ORDER BY product_id
                    LIMIT 100
                    """

                rows = await conn.fetch(query)
                products = []
                for row in rows:
                    products.append(
                        {
                            "product_id": str(row["product_id"]),
                            "name": row["name"],
                            "category": row["category"],
                            "description": row["description"],
                            "brand": row["brand"],
                            "type": row["type"],
                        }
                    )

                logger.info(f"Found {len(products)} products to sync")
                return products

        except Exception as e:
            logger.error(f"Error getting products to sync: {e}")
            return []

    async def update_products_sync_status(self, product_ids: List[str], indexed: bool):
        """Update sync status for products"""
        try:
            async with db_manager.get_connection() as conn:
                now = datetime.now()
                query = """
                UPDATE products_new
                SET qdrant_indexed = $1, qdrant_indexed_at = $2
                WHERE product_id = ANY($3::text[])
                """
                await conn.execute(query, indexed, now, product_ids)
                logger.info(f"Updated sync status for {len(product_ids)} products")
        except Exception as e:
            logger.error(f"Error updating product sync status: {e}")
            raise

    async def record_sync_completion(
        self,
        sync_id: str,
        started_at: datetime,
        completed_at: datetime,
        total: int,
        processed: int,
        failed: int,
    ):
        """Record sync completion (create table if needed)"""
        try:
            async with db_manager.get_connection() as conn:
                # Create table if not exists
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sync_history (
                        id SERIAL PRIMARY KEY,
                        sync_id UUID UNIQUE NOT NULL,
                        started_at TIMESTAMP NOT NULL,
                        completed_at TIMESTAMP NOT NULL,
                        duration_seconds FLOAT NOT NULL,
                        total_products INT NOT NULL,
                        processed_products INT NOT NULL,
                        failed_products INT NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Record sync
                duration = (completed_at - started_at).total_seconds()
                status = (
                    "success"
                    if failed == 0
                    else "partial" if processed > 0 else "failed"
                )

                await conn.execute(
                    """
                    INSERT INTO sync_history 
                    (sync_id, started_at, completed_at, duration_seconds, 
                     total_products, processed_products, failed_products, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    sync_id,
                    started_at,
                    completed_at,
                    duration,
                    total,
                    processed,
                    failed,
                    status,
                )

        except Exception as e:
            logger.error(f"Error recording sync completion: {e}")

    async def get_last_sync_info(self) -> Optional[dict]:
        """Get information about the last sync"""
        try:
            async with db_manager.get_connection() as conn:
                # Check if table exists
                table_exists = await conn.fetchval(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'sync_history'
                    )
                """
                )

                if not table_exists:
                    return None

                row = await conn.fetchrow(
                    """
                    SELECT sync_id, started_at, completed_at, duration_seconds,
                           total_products, processed_products, failed_products, status
                    FROM sync_history
                    ORDER BY started_at DESC
                    LIMIT 1
                """
                )

                if row:
                    return {
                        "sync_id": str(row["sync_id"]),
                        "started_at": row["started_at"].isoformat(),
                        "completed_at": row["completed_at"].isoformat(),
                        "duration_seconds": row["duration_seconds"],
                        "total_products": row["total_products"],
                        "processed_products": row["processed_products"],
                        "failed_products": row["failed_products"],
                        "status": row["status"],
                    }

                return None

        except Exception as e:
            logger.error(f"Error getting last sync info: {e}")
            return None
