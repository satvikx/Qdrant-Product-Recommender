from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    collection_info: Dict
    model_name: str


class Product(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    brand: str
    type: str
    qdrant_indexed: bool = False
    qdrant_indexed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductForEmbedding(BaseModel):
    product_id: str
    name: str
    category: str
    description: str
    brand: str
    type: str

    def to_text(self) -> str:
        """Convert product to text for embedding"""
        text_parts = [
            f"Product: {self.name}",
            f"Brand: {self.brand}",
            f"Category: {self.category}",
            f"Type: {self.type}",
            f"Description: {self.description}",
        ]
        return " | ".join(text_parts)


class ProductUpdate(BaseModel):
    product_id: str
    qdrant_indexed: bool
    qdrant_indexed_at: datetime
