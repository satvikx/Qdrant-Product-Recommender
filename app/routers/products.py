from fastapi import APIRouter, Depends, HTTPException
from app.utils.logging import logger
from app.models.recommendation import (
    SimilarProductsRequest,
    SimilarProductsResponse,
    SemanticQueryRequest,
    SemanticQueryResponse,
    SimilarProductsListRequest,
    SimilarProductsListResponse
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("/similar", response_model=SimilarProductsResponse)
async def get_similar_products(request: SimilarProductsRequest):
    """
    Get products similar to a given product ID

    This endpoint takes a product ID (int or string) and directly queries the
    vector database to find similar products based on vector similarity.
    Uses client.query_points() for direct vector similarity search.
    """
    try:
        service = RecommendationService()
        result = await service.get_similar_products_by_id(
            product_id=request.product_id,
            limit=request.limit,
            category_filter=request.category_filter,
            brand_filter=request.brand_filter,
        )

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return SimilarProductsResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_similar_products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/similar/list", response_model=SimilarProductsListResponse)
async def get_similar_products_from_list(request: SimilarProductsListRequest):
    """ Get products similar to a given list of product IDs

    This endpoint takes a list of product IDs (string) and directly queries the
    vector database to find similar products based on vector similarity.
    Uses client.query_points() for direct vector similarity search. """
    try:
        service = RecommendationService()
        result = await service.get_similar_products_from_list_of_ids(
            product_ids=request.product_ids,
            limit=request.limit,
            category_filter=request.category_filter,
            brand_filter=request.brand_filter,
        )

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])

        return SimilarProductsListResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_similar_products_from_list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/search", response_model=SemanticQueryResponse)
async def semantic_search(request: SemanticQueryRequest):
    """
    Search for products using semantic query

    This endpoint takes a text query, generates embeddings, and returns
    the most relevant products based on semantic similarity.
    """
    try:
        service = RecommendationService()
        result = await service.get_semantic_recommendations(
            query=request.query,
            limit=request.limit,
            category_filter=request.category_filter,
            brand_filter=request.brand_filter,
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])

        return SemanticQueryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in semantic_search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
