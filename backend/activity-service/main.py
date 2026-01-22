"""
Activity Service FastAPI Application

This module provides the REST API for the Activity Service using FastAPI.
It implements endpoints for managing pet activities with proper validation,
error handling, and documentation.
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from models import Activity, ActivityCreate, ActivitySearchFilters
from database import get_cosmos_service, ActivityCosmosService
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    Uses lazy initialization to avoid blocking startup if CosmosDB is not available
    """
    logger.info("🚀 Activity Service starting up...")
    logger.info(
        "Using lazy initialization - CosmosDB will be connected on first request")

    yield

    logger.info("🛑 Activity Service shutting down...")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="RESTful API for managing pet activities with Azure CosmosDB backend",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection for database service
def get_db_service() -> ActivityCosmosService:
    """Dependency to get database service instance"""
    return get_cosmos_service()

###############################################################################
# HEALTH CHECK ENDPOINT
###############################################################################

@app.get("/health", tags=["Health"])
async def health_check(db_service: ActivityCosmosService = Depends(get_db_service)):
    """
    Health check endpoint with auto-database setup

    If the database or container doesn't exist, they will be created automatically
    with sample activity data for immediate testing.
    """
    try:
        result = await db_service.health_check()
        return result
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"Service unavailable: {str(e)}")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "description": "RESTful API for managing pet activities",
        "endpoints": {
            "health": "/health",
            "activities": "/api/activities",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


###############################################################################
# ACTIVITY MANAGEMENT ENDPOINTS
###############################################################################

@app.get("/api/activities", response_model=List[Activity], tags=["Activities"])
async def get_activities(
    petId: Optional[str] = Query(None, description="Filter by pet ID"),
    type: Optional[str] = Query(
        None, description="Filter by activity type (feed|walk|play|vet|train)"),
    from_param: Optional[datetime] = Query(
        None, alias="from", description="Filter activities from this timestamp (ISO format)"),
    to: Optional[datetime] = Query(
        None, description="Filter activities to this timestamp (ISO format)"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db_service: ActivityCosmosService = Depends(get_db_service)
):
    """
    Get activities with optional filtering and pagination

    - **petId**: Filter activities for a specific pet
    - **type**: Filter by activity type (feed, walk, play, vet, train)
    - **from**: Filter activities from this timestamp (ISO format)
    - **to**: Filter activities to this timestamp (ISO format)  
    - **limit**: Maximum number of results (1-1000, default: 100)
    - **offset**: Number of results to skip for pagination (default: 0)
    """
    try:
        # Create search filters
        filters = ActivitySearchFilters(
            petId=petId,
            type=type,
            from_timestamp=from_param,
            to_timestamp=to,
            limit=limit,
            offset=offset
        )

        # If no filters provided, get all activities
        if not any([petId, type, from_param, to]):
            activities = await db_service.get_all_activities()
        else:
            activities = await db_service.search_activities(filters)

        # Apply client-side pagination if needed (for get_all_activities)
        if not any([petId, type, from_param, to]) and (offset > 0 or limit < 1000):
            end_index = offset + limit
            activities = activities[offset:end_index]

        return activities

    except Exception as e:
        logger.error(f"Error retrieving activities: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving activities: {str(e)}")


@app.post("/api/activities", response_model=Activity, status_code=201, tags=["Activities"])
async def create_activity(
    activity_data: ActivityCreate,
    db_service: ActivityCosmosService = Depends(get_db_service)
):
    """
    Create a new activity

    - **petId**: ID of the pet this activity belongs to (required)
    - **type**: Activity type - must be one of: feed, walk, play, vet, train (required)
    - **timestamp**: When the activity occurred (ISO format, required)
    - **notes**: Additional notes about the activity (optional, max 1000 chars)
    """
    try:
        activity = db_service.create_activity(activity_data)
        logger.info(f"Created activity {activity.id} for pet {activity.petId}")
        return activity

    except Exception as e:
        logger.error(f"Error creating activity: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error creating activity: {str(e)}")


@app.get("/api/activities/{activity_id}", response_model=Activity, tags=["Activities"])
async def get_activity(
    activity_id: str,
    db_service: ActivityCosmosService = Depends(get_db_service)
):
    """
    Get a specific activity by ID

    - **activity_id**: The unique identifier of the activity
    """
    try:
        activity = db_service.get_activity(activity_id)
        if not activity:
            raise HTTPException(
                status_code=404, detail=f"Activity with ID {activity_id} not found")

        return activity

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving activity {activity_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving activity: {str(e)}")


@app.delete("/api/activities/{activity_id}", tags=["Activities"])
async def delete_activity(
    activity_id: str,
    db_service: ActivityCosmosService = Depends(get_db_service)
):
    """
    Delete an activity by ID

    - **activity_id**: The unique identifier of the activity to delete
    """
    try:
        deleted = db_service.delete_activity(activity_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail=f"Activity with ID {activity_id} not found")

        logger.info(f"Deleted activity {activity_id}")
        return {"message": f"Activity {activity_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting activity {activity_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting activity: {str(e)}")


###############################################################################
# APPLICATION ENTRY POINT
###############################################################################

if __name__ == "__main__":
    import uvicorn

    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8020,  # Different port from Pet Service
        reload=True,
        log_level="info"
    )
