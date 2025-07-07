from app.config import settings
from qdrant_client import QdrantClient, models
from app.utils.logging import logger
from typing import Optional, List, Dict
from app.models.recommendation import ProductRecommendation
from qdrant_client.models import (
    Document,
)


class RecommendationService:
    def __init__(self):
        self.collection_name = settings.COLLECTION_NAME
        self.model_name = settings.MODEL_NAME
        self.client = QdrantClient(settings.QDRANT_URL, port=settings.QDRANT_PORT)

        logger.info(
            f"Initialized Qdrant client with collection: {self.collection_name} with model {self.model_name}"
        )

    async def get_similar_products_by_id(
        self,
        product_id: str,
        limit: int = 10,
        category_filter: Optional[str] = None,
        brand_filter: Optional[str] = None,
    ) -> Dict:
        """
        Get products similar to a given product ID by querying vector database directly
        """
        try:
            query_id = product_id

            # Build query filter for excluding the reference product
            must_not_filter = [{"key": "product_id", "match": {"value": product_id}}]

            # Build additional filters
            must_filter = []
            if category_filter:
                must_filter.append(
                    {"key": "category", "match": {"value": category_filter}}
                )
            if brand_filter:
                must_filter.append({"key": "brand", "match": {"value": brand_filter}})

            # Create filter object
            query_filter = None
            if must_filter or must_not_filter:
                filter_conditions = {}
                if must_filter:
                    filter_conditions["must"] = must_filter
                if must_not_filter:
                    filter_conditions["must_not"] = must_not_filter
                query_filter = filter_conditions

            # Query vector database directly using product ID
            similar_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_id,
                limit=limit,
                query_filter=query_filter,
            )

            # Format similar products
            similar_products = []
            for result in similar_results.points:
                recommendation = ProductRecommendation(
                    product_id=result.payload["product_id"],
                    name=result.payload["name"],
                    category=result.payload["category"],
                    brand=result.payload["brand"],
                    type=result.payload["type"],
                    description=result.payload["description"],
                    similarity_score=(
                        float(result.score) if hasattr(result, "score") else 0.0
                    ),
                )
                similar_products.append(recommendation)

            return {
                "success": True,
                # "time": similar_results.time,
                "message": f"Found {len(similar_products)} similar products",
                "reference_product": query_id,
                "similar_products": similar_products,
                "total_found": len(similar_products),
            }

        except Exception as e:
            logger.error(f"Error getting similar products: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving similar products: {str(e)}",
                "reference_product": None,
                "similar_products": [],
                "total_found": 0,
            }

    async def get_semantic_recommendations(
        self,
        query: str,
        limit: int = 10,
        category_filter: Optional[str] = None,
        brand_filter: Optional[str] = None,
    ) -> Dict:
        """
        Get product recommendations based on semantic query
        """
        try:
            # Build query filter
            query_filter = {}
            if category_filter:
                query_filter["category"] = category_filter
            if brand_filter:
                query_filter["brand"] = brand_filter

            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=Document(text=query, model=self.model_name),
                limit=limit,
                query_filter=query_filter if query_filter else None,
            ).points

            # Format results
            recommendations = []
            for result in search_results:
                recommendation = ProductRecommendation(
                    product_id=result.payload["product_id"],
                    name=result.payload["name"],
                    category=result.payload["category"],
                    brand=result.payload["brand"],
                    type=result.payload["type"],
                    description=result.payload["description"],
                    similarity_score=float(result.score),
                )
                recommendations.append(recommendation)

            return {
                "success": True,
                "message": f"Found {len(recommendations)} recommendations",
                "query": query,
                "recommendations": recommendations,
                "total_found": len(recommendations),
            }

        except Exception as e:
            logger.error(f"Error getting semantic recommendations: {str(e)}")
            return {
                "success": False,
                "message": f"Error retrieving recommendations: {str(e)}",
                "query": query,
                "recommendations": [],
                "total_found": 0,
            }
