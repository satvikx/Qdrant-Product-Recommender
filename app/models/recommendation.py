from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class ProductRecommendation(BaseModel):
    product_id: UUID
    name: str
    category: str
    brand: str
    type: str
    description: str
    similarity_score: float

class SimilarProductsRequest(BaseModel):
    product_id: str = Field(
        ..., description="Product ID to find similar products for"
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Number of similar products to return"
    )
    category_filter: Optional[str] = Field(None, description="Optional category filter")
    brand_filter: Optional[str] = Field(None, description="Optional brand filter")

class SimilarProductsResponse(BaseModel):
    success: bool
    message: str
    reference_product: str
    similar_products: List[ProductRecommendation]
    total_found: int

class SimilarProductsListRequest(BaseModel):
    product_ids: List[str] = Field(
        ..., description="List of Product IDs to find similar products for"
    )
    limit: int = Field(
        default=10, ge=1, le=50, description="Number of similar products to return"
    )
    category_filter: Optional[str] = Field(None, description="Optional category filter")
    brand_filter: Optional[str] = Field(None, description="Optional brand filter")

class SimilarProductsListResponse(BaseModel):
    success: bool
    message: str
    reference_products: List[str]
    similar_products: List[ProductRecommendation]
    total_found: int

class SemanticQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(
        default=10, ge=1, le=50, description="Number of recommendations to return"
    )
    category_filter: Optional[str] = Field(None, description="Optional category filter")
    brand_filter: Optional[str] = Field(None, description="Optional brand filter")

class SemanticQueryResponse(BaseModel):
    success: bool
    message: str
    query: str
    recommendations: List[ProductRecommendation]
    total_found: int
