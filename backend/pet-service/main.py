"""
FastAPI Pet Service API

This module implements a REST API for pet management using FastAPI and Azure CosmosDB.
Follows Azure best practices for authentication, error handling, and API design.
"""

import logging
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import get_settings
from models import Pet, PetCreate, PetUpdate, PetSearchFilters
from database import get_cosmos_service, CosmosDBService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Pet Service API")
    logger.info("CosmosDB connection will be established when first needed")

    yield

    # Shutdown
    logger.info("Shutting down Pet Service API")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Pet management API with Azure CosmosDB backend",
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
def get_db() -> CosmosDBService:
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
async def health_check(db: CosmosDBService = Depends(get_db)):
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


@app.get("/clean", tags=["Maintenance"])
async def clean_database(db: CosmosDBService = Depends(get_db)):
    """Delete the configured CosmosDB database and leave the service empty."""
    try:
        result = await db.clean_database()
        if result.get("status") != "clean":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to clean CosmosDB")
            )

        logger.info("CosmosDB environment reset for challenge setup")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning CosmosDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean CosmosDB"
        )


@app.get("/api/pets", response_model=List[Pet], tags=["Pets"])
async def get_pets(
    search: Optional[str] = Query(
        None, description="Search term for name or notes"),
    species: Optional[str] = Query(
        None, description="Filter by species (dog, cat, bird, other)"),
    status: Optional[str] = Query(
        None, description="Filter by status (reserved for future use)"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: CosmosDBService = Depends(get_db)
):
    """
    Get pets with optional filtering and pagination

    - **search**: Search in pet names and notes
    - **species**: Filter by pet species (dog, cat, bird, other)
    - **status**: Reserved for future use
    - **limit**: Maximum number of results (1-1000)
    - **offset**: Number of results to skip for pagination
    """
    try:
        # Validate species filter
        if species and species not in ["dog", "cat", "bird", "other"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid species. Must be one of: dog, cat, bird, other"
            )

        # Create search filters
        filters = PetSearchFilters(
            search=search,
            species=species,
            status=status,
            limit=limit,
            offset=offset
        )

        logger.info(f"Searching pets with filters: {filters.model_dump()}")
        # Search pets
        pets = await db.search_pets(filters)

        logger.info(
            f"Retrieved {len(pets)} pets with filters: {filters.model_dump()}")
        return pets

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pets"
        )


@app.post("/api/pets", response_model=Pet, status_code=status.HTTP_201_CREATED, tags=["Pets"])
def create_pet(
    pet_data: PetCreate,
    db: CosmosDBService = Depends(get_db)
):
    """
    Create a new pet

    - **name**: Pet name (required)
    - **species**: Pet species - dog, cat, bird, or other (required)
    - **ageYears**: Pet age in years (0-50)
    - **health**: Health level (0-100)
    - **happiness**: Happiness level (0-100)
    - **energy**: Energy level (0-100)
    - **avatarUrl**: URL to pet avatar image (optional)
    - **notes**: Additional notes about the pet (optional)
    """
    try:
        pet = db.create_pet(pet_data)
        logger.info(f"Created new pet: {pet.id}")
        return pet

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating pet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create pet"
        )


@app.get("/api/pets/{pet_id}", response_model=Pet, tags=["Pets"])
def get_pet(
    pet_id: str,
    db: CosmosDBService = Depends(get_db)
):
    """
    Get a specific pet by ID

    - **pet_id**: Unique pet identifier
    """
    try:
        pet = db.get_pet(pet_id)
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found"
            )

        return pet

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving pet {pet_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pet"
        )


@app.patch("/api/pets/{pet_id}", response_model=Pet, tags=["Pets"])
def update_pet(
    pet_id: str,
    update_data: PetUpdate,
    db: CosmosDBService = Depends(get_db)
):
    """
    Update a pet by ID (partial update)

    - **pet_id**: Unique pet identifier
    - **Update fields**: Any combination of pet fields to update
    """
    try:
        pet = db.update_pet(pet_id, update_data)
        if not pet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found"
            )

        logger.info(f"Updated pet: {pet_id}")
        return pet

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating pet {pet_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update pet"
        )


@app.delete("/api/pets/{pet_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Pets"])
def delete_pet(
    pet_id: str,
    db: CosmosDBService = Depends(get_db)
):
    """
    Delete a pet by ID

    - **pet_id**: Unique pet identifier
    """
    try:
        deleted = db.delete_pet(pet_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pet with ID {pet_id} not found"
            )

        logger.info(f"Deleted pet: {pet_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pet {pet_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete pet"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=settings.debug,
        log_level="info"
    )
