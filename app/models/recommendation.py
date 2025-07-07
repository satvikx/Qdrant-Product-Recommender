from pydantic import BaseModel, Field
from typing import Optional, List


class ProductRecommendation(BaseModel):
    product_id: int
    name: str
    category: str
    brand: str
    type: str
    description: str
    similarity_score: float


class SimilarProductsRequest(BaseModel):
    product_id: int = Field(
        ..., description="Product ID (int) to find similar products for"
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Number of similar products to return"
    )
    category_filter: Optional[str] = Field(None, description="Optional category filter")
    brand_filter: Optional[str] = Field(None, description="Optional brand filter")


class SemanticQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    )
    category_filter: Optional[str] = Field(None, description="Optional category filter")
    brand_filter: Optional[str] = Field(None, description="Optional brand filter")


class SimilarProductsResponse(BaseModel):
    success: bool
    message: str
    reference_product: int
    similar_products: List[ProductRecommendation]
    total_found: int


class SemanticQueryResponse(BaseModel):
    success: bool
    message: str
    query: str
    recommendations: List[ProductRecommendation]
    total_found: int
