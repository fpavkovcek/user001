"""
Accessory Service FastAPI Application

This module implements a REST API for accessory management using FastAPI and Azure CosmosDB.
Follows Azure best practices for authentication, error handling, and API design.
"""

import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from models import Accessory, AccessoryCreate, AccessoryUpdate, AccessorySearchFilters
from database import get_cosmos_service, AccessoryCosmosService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Accessory Service API")
    logger.info("CosmosDB connection will be established when first needed")

    yield

    # Shutdown
    logger.info("Shutting down Accessory Service API")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Accessory management API with Azure CosmosDB backend",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get CosmosDB service
def get_db() -> AccessoryCosmosService:
    """Dependency to get CosmosDB service instance"""
    return get_cosmos_service()


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred"}
    )


# API Routes

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check(db: AccessoryCosmosService = Depends(get_db)):
    """Health check endpoint"""
    try:
        cosmos_health = await db.health_check()
        return {
            "status": "healthy",
            "version": settings.app_version,
            "database": cosmos_health
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )


@app.get("/api/accessories", response_model=List[Accessory], tags=["Accessories"])
async def get_accessories(
    search: Optional[str] = Query(
        None, description="Search term for name or description"),
    type: Optional[str] = Query(
        None, description="Filter by accessory type (toy, food, collar, bedding, grooming, other)"),
    lowStockOnly: Optional[bool] = Query(
        None, description="Show only low stock items (stock < 10)"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AccessoryCosmosService = Depends(get_db)
):
    """
    Get accessories with optional filtering and pagination

    - **search**: Search in accessory names and descriptions
    - **type**: Filter by accessory type (toy, food, collar, bedding, grooming, other)
    - **lowStockOnly**: Show only items with stock < 10
    - **limit**: Maximum number of results (1-1000)
    - **offset**: Number of results to skip for pagination
    """
    try:
        # Validate type filter
        valid_types = ["toy", "food", "collar", "bedding", "grooming", "other"]
        if type and type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type. Must be one of: {', '.join(valid_types)}"
            )

        # Create search filters
        filters = AccessorySearchFilters(
            search=search,
            type=type,
            lowStockOnly=lowStockOnly,
            limit=limit,
            offset=offset
        )

        # Search accessories
        accessories = await db.search_accessories(filters)

        logger.info(
            f"Retrieved {len(accessories)} accessories with filters: {filters.model_dump()}")
        return accessories

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving accessories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accessories"
        )


@app.post("/api/accessories", response_model=Accessory, status_code=status.HTTP_201_CREATED, tags=["Accessories"])
def create_accessory(
    accessory_data: AccessoryCreate,
    db: AccessoryCosmosService = Depends(get_db)
):
    """
    Create a new accessory

    - **name**: Accessory name (required)
    - **type**: Accessory type - toy, food, collar, bedding, grooming, or other (required)
    - **price**: Price (required, >= 0)
    - **stock**: Stock quantity (required, >= 0)
    - **size**: Size - S, M, L, or XL (required)
    - **imageUrl**: URL to accessory image (optional)
    - **description**: Description of the accessory (optional)
    """
    try:
        accessory = db.create_accessory(accessory_data)
        logger.info(f"Created new accessory: {accessory.id}")
        return accessory

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating accessory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create accessory"
        )


@app.get("/api/accessories/{accessory_id}", response_model=Accessory, tags=["Accessories"])
def get_accessory(
    accessory_id: str,
    db: AccessoryCosmosService = Depends(get_db)
):
    """
    Get a specific accessory by ID

    - **accessory_id**: Unique accessory identifier
    """
    try:
        accessory = db.get_accessory(accessory_id)
        if not accessory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Accessory with ID {accessory_id} not found"
            )

        return accessory

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving accessory {accessory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accessory"
        )


@app.patch("/api/accessories/{accessory_id}", response_model=Accessory, tags=["Accessories"])
def update_accessory(
    accessory_id: str,
    update_data: AccessoryUpdate,
    db: AccessoryCosmosService = Depends(get_db)
):
    """
    Update an accessory by ID (partial update)

    - **accessory_id**: Unique accessory identifier
    - **Update fields**: Any combination of accessory fields to update
    """
    try:
        accessory = db.update_accessory(accessory_id, update_data)
        if not accessory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Accessory with ID {accessory_id} not found"
            )

        logger.info(f"Updated accessory: {accessory_id}")
        return accessory

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating accessory {accessory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update accessory"
        )


@app.delete("/api/accessories/{accessory_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Accessories"])
def delete_accessory(
    accessory_id: str,
    db: AccessoryCosmosService = Depends(get_db)
):
    """
    Delete an accessory by ID

    - **accessory_id**: Unique accessory identifier
    """
    try:
        deleted = db.delete_accessory(accessory_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Accessory with ID {accessory_id} not found"
            )

        logger.info(f"Deleted accessory: {accessory_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting accessory {accessory_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete accessory"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8030,  # Different port from Pet and Activity Services
        reload=settings.debug,
        log_level="info"
    )
