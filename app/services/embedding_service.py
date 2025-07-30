from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Batch
from typing import List, Dict, Optional
import logging
from app.config import settings
from app.models.product import ProductForEmbedding
from app.utils.logging import logger
from fastembed import TextEmbedding

import google.generativeai as genai


class EmbeddingService:
    def __init__(self):
        self.client = QdrantClient(settings.QDRANT_URL, port=settings.QDRANT_PORT)
        self.model_name = settings.MODEL_NAME
        # self.client.set_model(settings.MODEL_NAME)
        self.collection_name = settings.COLLECTION_NAME
        self.embedding_model = TextEmbedding(
            model_name=self.model_name, cache_dir=".cache"
        )
        logger.info(f"Initialized EmbeddingService with model: {self.model_name}")
        # genai.configure(api_key="AIzaSyAEnN3M1Ugw-uVyt5BdtQ8lziogsNCcwjw")

    async def ensure_collection_exists(self):
        """Ensure collection exists, create if not"""
        try:
            if not self.client.collection_exists(collection_name=self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.client.get_embedding_size(self.model_name),
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created Collection : {self.collection_name}")
                return True

            logger.info(f"Collection {self.collection_name} already exists")
            return True
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            return False

    def get_embeddings(self, documents: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings using fastembed.TextEmbedding
        """
        try:
            # embed() returns a generator
            return list(self.embedding_model.embed(documents))
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    # TODO: This was just for experimentation and is not called elsewhere
    def get_embeddings_gemini(self, documents: list[str]) -> list[list[float]]:
        """
        Generate embeddings using Google Gemini Embeddings API authenticated via API key.
        """
        try:
            response = genai.embed_content(
                model="gemini-embedding-001",
                content=documents,
                task_type="SEMANTIC_SIMILARITY",
                output_dimensionality=384,
            )
            embeddings = [list(item) for item in response["embedding"]]
            print(f"Generated {len(embeddings)} embeddings with gemini.")
            return embeddings

        except Exception as e:
            logger.error(f"Embedding generation failed with Google Gemini API: {e}")
            raise

    async def add_products_to_vector_db(
        self, products: List["ProductForEmbedding"]
    ) -> tuple[List[str], List[str]]:
        """
        Upsert products into Qdrant using batch operation.
        Returns: (successful_ids, failed_ids)
        """
        successful_ids = []
        failed_ids = []

        if not products:
            return successful_ids, failed_ids

        try:
            documents = []
            payloads = []
            ids = []

            for product in products:
                try:
                    doc_text = product.to_text()
                    documents.append(doc_text)
                    payloads.append(
                        {
                            "product_id": product.product_id,
                            "name": product.name,
                            "category": product.category,
                            "brand": product.brand,
                            "type": product.type,
                            "description": product.description,
                        }
                    )
                    ids.append(str(product.product_id))
                except Exception as e:
                    logger.error(f"Error preparing product {product.product_id}: {e}")
                    failed_ids.append(product.product_id)

            # Generate embeddings using fastembed
            try:
                vectors = self.get_embeddings(documents)

            except Exception as e:
                logger.error("Failed to generate the embeddings : " + e)

            if vectors:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=Batch(ids=ids, vectors=vectors, payloads=payloads),
                )
                successful_ids.extend([pid for pid in ids if pid not in failed_ids])
                logger.info(
                    f"Successfully upserted {len(successful_ids)} products to Qdrant"
                )
        except Exception as e:
            logger.error(f"Error during Qdrant upsert: {e}")
            failed_ids.extend(
                [p.product_id for p in products if p.product_id not in failed_ids]
            )

        return successful_ids, failed_ids

    async def add_products_to_vector_db_old(
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
                    ids.append(product.product_id)
                    # Convert to int if possible, otherwise use string
                    # try:
                    #     ids.append(int(product.product_id))
                    # except ValueError:
                    #     ids.append(product.product_id)
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
            info_detail = info.config.params.vectors
            return {
                "collection_name": self.collection_name,
                "points_count": info.points_count,
                "vector_size": (
                    info_detail.size
                    if hasattr(info.config.params, "vectors")
                    else "unknown"
                ),
                "distance_metric": (
                    str(info_detail.distance)
                    if hasattr(info.config.params, "vectors")
                    else "unknown"
                ),
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
