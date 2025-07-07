from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from typing import List, Dict, Optional
import logging
from app.config import settings
from app.models.product import ProductForEmbedding

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.client = QdrantClient(settings.QDRANT_URL, port=settings.QDRANT_PORT)
        self.client.set_model(settings.MODEL_NAME)
        self.collection_name = settings.COLLECTION_NAME
        logger.info(f"Initialized EmbeddingService with model: {settings.MODEL_NAME}")

    async def ensure_collection_exists(self):
        """Ensure collection exists, create if not"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                # Let FastEmbed handle collection creation automatically
                return True

            logger.info(f"Collection {self.collection_name} already exists")
            return True
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            return False

    async def add_products_to_vector_db(
        self, products: List[ProductForEmbedding]
    ) -> tuple[List[str], List[str]]:
        """
        Add products to vector database
        Returns: (successful_ids, failed_ids)
        """
        successful_ids = []
        failed_ids = []

        if not products:
            return successful_ids, failed_ids

        try:
            # Prepare data for Qdrant
            documents = []
            metadata = []
            ids = []

            for product in products:
                try:
                    documents.append(product.to_text())
                    metadata.append(
                        {
                            "product_id": product.product_id,
                            "name": product.name,
                            "category": product.category,
                            "brand": product.brand,
                            "type": product.type,
                            "description": product.description,
                        }
                    )
                    # Convert to int if possible, otherwise use string
                    try:
                        ids.append(int(product.product_id))
                    except ValueError:
                        ids.append(product.product_id)
                except Exception as e:
                    logger.error(f"Error preparing product {product.product_id}: {e}")
                    failed_ids.append(product.product_id)

            # Upload to Qdrant
            if documents:
                self.client.add(
                    collection_name=self.collection_name,
                    documents=documents,
                    metadata=metadata,
                    ids=ids,
                )

                # All successful if no exception
                successful_ids.extend(
                    [p.product_id for p in products if p.product_id not in failed_ids]
                )

                logger.info(
                    f"Successfully added {len(successful_ids)} products to vector DB"
                )

        except Exception as e:
            logger.error(f"Error adding products to vector DB: {e}")
            # Mark all as failed
            failed_ids.extend(
                [p.product_id for p in products if p.product_id not in failed_ids]
            )

        return successful_ids, failed_ids

    async def test_connection(self) -> tuple[bool, str]:
        """Test Qdrant connection"""
        try:
            collections = self.client.get_collections()
            return (
                True,
                f"Connected successfully. Found {len(collections.collections)} collections.",
            )
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    async def get_collection_info(self) -> Dict:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "vector_size": (
                    info.config.params.vectors["fast-bge-small-en-v1.5"]
                    if hasattr(info.config.params, "vectors")
                    else "unknown"
                ),
                "distance_metric": (
                    str(info.config.params.vectors.distance)
                    if hasattr(info.config.params, "vectors")
                    else "unknown"
                ),
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
