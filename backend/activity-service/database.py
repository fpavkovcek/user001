"""
Activity Service Database Layer

This module provides the database service layer for activities using Azure CosmosDB.
It follows Azure best practices for CosmosDB integration with proper error handling,
logging, and performance optimization.

Authentication Strategy:
- Local Development (localhost): Uses key-based authentication with emulator
- Azure Deployment: Uses Entra ID (Managed Identity) authentication
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos import exceptions as cosmos_exceptions
from azure.identity import DefaultAzureCredential
from models import Activity, ActivityCreate, ActivityUpdate, ActivitySearchFilters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActivityCosmosService:
    """
    Service class for managing activities in Azure CosmosDB

    This class provides CRUD operations and search capabilities for activities,
    following Azure CosmosDB best practices for partition key usage and query optimization.
    """

    def __init__(self, cosmos_endpoint: str, cosmos_key: str, database_name: str = "activityservice", container_name: str = "activities"):
        """
        Initialize the CosmosDB service

        Args:
            cosmos_endpoint: Azure CosmosDB endpoint URL
            cosmos_key: Azure CosmosDB access key
            database_name: CosmosDB database name
            container_name: CosmosDB container name
        """
        self.cosmos_endpoint = cosmos_endpoint
        self.cosmos_key = cosmos_key
        self.database_name = database_name
        self.container_name = container_name

        # Initialize client, database, and container as None (lazy initialization)
        self.client = None
        self.database = None
        self.container = None

        logger.info("ActivityCosmosService initialized with lazy loading")

    def _build_cosmos_client_options(self) -> Dict[str, Any]:
        """
        Build CosmosClient configuration for consistent usage across services.

        Authentication strategy:
        - Local (localhost): Key-based authentication with optional SSL verification disabled
        - Azure: Entra ID (Managed Identity) authentication via DefaultAzureCredential
        """
        # Detect if running locally
        is_local = "localhost" in self.cosmos_endpoint.lower(
        ) or "127.0.0.1" in self.cosmos_endpoint

        options: Dict[str, Any] = {
            "url": self.cosmos_endpoint,
            "connection_timeout": 30,
            "request_timeout": 30,
        }

        if is_local:
            # Local development: Use key-based authentication
            logger.info("Using key-based authentication (local development)")
            options["credential"] = self.cosmos_key

            # Check if SSL verification should be disabled (for emulator)
            disable_ssl_verify = os.getenv(
                "COSMOS_EMULATOR_DISABLE_SSL_VERIFY", "0").lower() in ("1", "true", "yes")

            if disable_ssl_verify:
                options["connection_verify"] = False  # type: ignore[arg-type]
                logger.warning(
                    "COSMOS_EMULATOR_DISABLE_SSL_VERIFY is enabled – SSL certificate verification DISABLED (dev/emulator only)")
        else:
            # Azure deployment: Use Entra ID (Managed Identity) authentication
            logger.info(
                "Using Entra ID authentication (Azure deployment with Managed Identity)")
            credential = DefaultAzureCredential()
            options["credential"] = credential

        return options

    def _ensure_initialized(self):
        """Ensure the CosmosDB client, database, and container are initialized"""
        if self.client is None:
            logger.info("Initializing CosmosDB client...")
            cosmos_client_options = self._build_cosmos_client_options()
            endpoint = cosmos_client_options["url"]
            if endpoint.startswith("http://"):
                logger.warning(
                    "cosmos_endpoint uses http:// – prefer https:// for production parity.")
            self.client = CosmosClient(**cosmos_client_options)

        if self.database is None:
            logger.info(f"Getting database: {self.database_name}")
            self.database = self.client.get_database_client(self.database_name)

        if self.container is None:
            logger.info(f"Getting container: {self.container_name}")
            self.container = self.database.get_container_client(
                self.container_name)

    async def health_check(self) -> dict:
        """
        Perform health check and auto-create database/container if needed

        Returns:
            Dictionary with health status and any setup messages
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Try to perform a simple query to verify connection
            try:
                items = list(self.container.query_items(
                    query="SELECT TOP 1 c.id FROM c",
                    enable_cross_partition_query=True,
                    max_item_count=1
                ))

                if items:
                    return {"status": "healthy", "database": self.database_name}

                logger.info(
                    "Database is reachable but empty. Seeding with sample data...")
                await self._database_seed()
                return {
                    "status": "healthy",
                    "database": self.database_name,
                    "message": "Database was empty and has been seeded with sample data"
                }

            except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
                # Database or container doesn't exist - check if it's a "not found" type error
                error_message = str(e).lower()
                if "does not exist" in error_message or "notfound" in error_message or (hasattr(e, 'status_code') and e.status_code in [404, 500]):
                    logger.info(
                        "Database or container not found. Creating and seeding with sample data...")
                    result = await self._create_database_and_seed()
                    if result["status"] == "healthy":
                        return {
                            "status": "healthy",
                            "database": self.database_name,
                            "message": "Database and container created successfully with sample data"
                        }
                    else:
                        return result
                else:
                    # Re-raise if it's a different type of error
                    raise

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def _create_database_and_seed(self) -> dict:
        """Create database, container, and seed with sample activity data"""
        try:
            # Create database if it doesn't exist
            logger.info(f"Creating database: {self.database_name}")
            database = self.client.create_database_if_not_exists(
                id=self.database_name
            )

            # Create container if it doesn't exist
            logger.info(f"Creating container: {self.container_name}")
            container = database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400  # Minimum RU/s for manual throughput
            )

            # Update our references
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(
                self.container_name)

            await self._database_seed()
            logger.info("Database setup and seeding completed successfully")
            return {
                "status": "healthy",
                "message": "Database and container created successfully with sample data"
            }

        except Exception as e:
            logger.error(f"Failed to create database and seed data: {e}")
            return {"status": "unhealthy", "error": f"Failed to create database: {e}"}

    async def _database_seed(self) -> None:
        """Seed the existing CosmosDB container with sample activity data."""
        if self.container is None:
            raise RuntimeError(
                "Cosmos container is not initialized; cannot seed database")

        logger.info("Seeding container with sample activity data")
        sample_activities = [
            {
                "id": "a1",
                "petId": "p1",
                "type": "walk",
                "timestamp": "2025-10-05T08:30:00Z",
                "notes": "Park loop",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            },
            {
                "id": "a2",
                "petId": "p2",
                "type": "feed",
                "timestamp": "2025-10-05T07:00:00Z",
                "notes": "Tuna pouch",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            },
            {
                "id": "a3",
                "petId": "p1",
                "type": "play",
                "timestamp": "2025-10-04T18:00:00Z",
                "notes": "Frisbee",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        ]

        # Insert sample activities
        for activity_data in sample_activities:
            try:
                self.container.create_item(body=activity_data)
                logger.info(
                    f"Seeded activity: {activity_data['id']} - {activity_data['type']} ({activity_data['notes']})")
            except cosmos_exceptions.CosmosResourceExistsError:
                logger.info(
                    f"Activity {activity_data['id']} already exists, skipping")
                continue

    def create_activity(self, activity_data: ActivityCreate) -> Activity:
        """
        Create a new activity in CosmosDB

        Args:
            activity_data: Activity creation data

        Returns:
            Created Activity object

        Raises:
            CosmosHttpResponseError: If there's an error creating the activity
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Create Activity object with generated ID and timestamps
            activity = Activity(
                **activity_data.model_dump(),
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )

            # Convert to dictionary for CosmosDB (with JSON serialization)
            activity_dict = activity.model_dump(mode='json')

            # Create item in CosmosDB
            response = self.container.create_item(body=activity_dict)
            logger.info(f"Created activity: {response['id']}")

            return Activity(**response)

        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error creating activity: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating activity: {e}")
            raise

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """
        Get a specific activity by ID

        Args:
            activity_id: The activity ID to retrieve

        Returns:
            Activity object if found, None otherwise
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Read item from CosmosDB using ID as partition key
            response = self.container.read_item(
                item=activity_id, partition_key=activity_id)
            logger.info(f"Retrieved activity: {activity_id}")

            return Activity(**response)

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Activity not found: {activity_id}")
            return None
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(
                f"CosmosDB HTTP error retrieving activity {activity_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving activity {activity_id}: {e}")
            raise

    async def get_all_activities(self) -> List[Activity]:
        """
        Get all activities from CosmosDB

        Returns:
            List of Activity objects
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Query all activities ordered by timestamp (most recent first)
            query = "SELECT * FROM c ORDER BY c.timestamp DESC"

            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            logger.info(f"Retrieved {len(items)} activities")

            # Convert to Activity objects
            activities = []
            for item in items:
                try:
                    activities.append(Activity(**item))
                except Exception as e:
                    logger.warning(f"Failed to parse activity item: {e}")
                    continue

            return activities

        except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
            # Database or container doesn't exist - check if it's a "not found" type error
            error_message = str(e).lower()
            if "does not exist" in error_message or "notfound" in error_message or (hasattr(e, 'status_code') and e.status_code in [404, 500]):
                logger.info(
                    "Database or container not found during get_all. Creating and seeding with sample data...")
                await self._create_database_and_seed()
                # Retry after creating the database
                return await self.get_all_activities()
            else:
                logger.error(f"CosmosDB HTTP error retrieving activities: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving activities: {e}")
            raise

    async def search_activities(self, filters: ActivitySearchFilters) -> List[Activity]:
        """
        Search activities with filters and pagination

        Args:
            filters: Search and filter parameters

        Returns:
            List of Activity objects matching the criteria
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Build SQL query based on filters
            query_parts = ["SELECT * FROM c"]
            parameters = []
            conditions = []

            # Add petId filter
            if filters.petId:
                conditions.append("c.petId = @petId")
                parameters.append({"name": "@petId", "value": filters.petId})

            # Add activity type filter
            if filters.type:
                conditions.append("c.type = @type")
                parameters.append({"name": "@type", "value": filters.type})

            # Add timestamp range filters
            if filters.from_timestamp:
                conditions.append("c.timestamp >= @from_timestamp")
                parameters.append(
                    {"name": "@from_timestamp", "value": filters.from_timestamp.isoformat()})

            if filters.to_timestamp:
                conditions.append("c.timestamp <= @to_timestamp")
                parameters.append(
                    {"name": "@to_timestamp", "value": filters.to_timestamp.isoformat()})

            # Add WHERE clause if there are conditions
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            # Add ordering and pagination
            query_parts.append("ORDER BY c.timestamp DESC")
            query_parts.append(
                f"OFFSET {filters.offset} LIMIT {filters.limit}")

            query = " ".join(query_parts)
            logger.debug(
                f"Executing query: {query} with parameters: {parameters}")

            # Execute query
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=filters.limit
            ))

            # Convert to Activity objects
            activities = []
            for item in items:
                try:
                    activities.append(Activity(**item))
                except Exception as e:
                    logger.warning(f"Failed to parse activity item: {e}")
                    continue

            logger.info(f"Search returned {len(activities)} activities")
            return activities

        except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
            # Database or container doesn't exist - check if it's a "not found" type error
            error_message = str(e).lower()
            if "does not exist" in error_message or "notfound" in error_message or (hasattr(e, 'status_code') and e.status_code in [404, 500]):
                logger.info(
                    "Database or container not found during search. Creating and seeding with sample data...")
                await self._create_database_and_seed()
                # Retry the search after creating the database
                return await self.search_activities(filters)
            else:
                logger.error(f"CosmosDB HTTP error searching activities: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error searching activities: {e}")
            raise

    def delete_activity(self, activity_id: str) -> bool:
        """
        Delete an activity by ID

        Args:
            activity_id: The activity ID to delete

        Returns:
            True if deleted successfully, False if not found
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()

            # Delete item from CosmosDB
            self.container.delete_item(
                item=activity_id, partition_key=activity_id)
            logger.info(f"Deleted activity: {activity_id}")

            return True

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Activity not found for deletion: {activity_id}")
            return False
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(
                f"CosmosDB HTTP error deleting activity {activity_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error deleting activity {activity_id}: {e}")
            raise


# Service instance factory
def get_cosmos_service() -> ActivityCosmosService:
    """
    Factory function to create and return a CosmosDB service instance

    Returns:
        ActivityCosmosService instance configured with environment variables
    """
    from config import get_settings
    settings = get_settings()

    return ActivityCosmosService(
        cosmos_endpoint=settings.cosmos_endpoint,
        cosmos_key=settings.cosmos_key,
        database_name=settings.cosmos_database_name,
        container_name=settings.cosmos_container_name
    )
