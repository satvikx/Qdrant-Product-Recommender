from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.utils.logging import logger
import uvicorn
from app.models.product import HealthResponse
from app.services.embedding_service import EmbeddingService
from app.config import settings
from app.routers import admin, products
from app.database import db_manager
from qdrant_client import QdrantClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the startup and shutdown events of the FastAPI application.
    Initializes clients, loads models on startup, and closes resources on shutdown.
    """
    logger.info("Application startup initiated (via lifespan).")
    try:
        # --- Startup Logic ---
        # client = await QdrantClient(settings.QDRANT_URL, port=settings.QDRANT_PORT)
        await db_manager.create_pool()
        logger.info("✅ Database client initialized.")

        yield  # This is where the application starts serving requests

    except Exception as e:
        logger.exception(
            "❌ Failed to initialize application services during startup. Application may not function correctly."
        )

    finally:
        # --- Shutdown Logic (runs after yield, even if errors occur during startup) ---
        logger.info("Application shutdown initiated (via lifespan).")


# Initialize FastAPI app
app = FastAPI(
    title="Products Recommender",
    version="v1",
    description="Product Recommendation System API with Vector Embeddings on Qdrant",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
app.include_router(admin.router)
app.include_router(products.router)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Product Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "similar_products": "/api/v1/products/similar",
            "semantic_search": "/api/v1/products/search",
            "admin_sync": "/api/v1/admin/sync",
            "admin_sync_status": "/api/v1/admin/sync/status",
            "docs": "/docs",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        service = EmbeddingService()
        collection_info = await service.get_collection_info()
        return HealthResponse(
            status="healthy",
            collection_info=collection_info,
            model_name=service.model_name,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


if __name__ == "__main__":
    # For development
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
