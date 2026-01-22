"""
Azure CosmosDB Service for Accessory Management

This module provides the database service layer for accessories using Azure CosmosDB.
It mirrors the implementation used by the activity service to ensure consistent
initialization, error handling, and search capabilities.

Authentication Strategy:
- Local Development (localhost): Uses key-based authentication with emulator
- Azure Deployment: Uses Entra ID (Managed Identity) authentication
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos import exceptions as cosmos_exceptions
from azure.identity import DefaultAzureCredential

from models import Accessory, AccessoryCreate, AccessoryUpdate, AccessorySearchFilters

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AccessoryCosmosService:
    """Service class for managing accessories in Azure CosmosDB."""

    def __init__(
        self,
        cosmos_endpoint: str,
        cosmos_key: str,
        database_name: str = "accessoryservice",
        container_name: str = "accessories",
    ):
        """Initialize the CosmosDB service for accessories."""
        self.cosmos_endpoint = cosmos_endpoint
        self.cosmos_key = cosmos_key
        self.database_name = database_name
        self.container_name = container_name

        self.client: Optional[CosmosClient] = None
        self.database = None
        self.container = None

        logger.info("AccessoryCosmosService initialized with lazy loading")

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
                    "COSMOS_EMULATOR_DISABLE_SSL_VERIFY is enabled – SSL certificate verification DISABLED (dev/emulator only)"
                )
        else:
            # Azure deployment: Use Entra ID (Managed Identity) authentication
            logger.info(
                "Using Entra ID authentication (Azure deployment with Managed Identity)")
            credential = DefaultAzureCredential()
            options["credential"] = credential

        return options

    def _ensure_initialized(self):
        """Ensure the CosmosDB client, database, and container are initialized."""
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

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and auto-create database/container if needed."""
        try:
            self._ensure_initialized()

            try:
                items = list(
                    self.container.query_items(
                        query="SELECT TOP 1 c.id FROM c",
                        enable_cross_partition_query=True,
                        max_item_count=1,
                    )
                )

                if items:
                    return {"status": "healthy", "database": self.database_name}

                logger.info(
                    "Database is reachable but empty. Seeding with sample data...")
                await self._database_seed()
                return {
                    "status": "healthy",
                    "database": self.database_name,
                    "message": "Database was empty and has been seeded with sample data",
                }
            except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
                error_message = str(e).lower()
                if "does not exist" in error_message or "notfound" in error_message or (
                    hasattr(e, "status_code") and e.status_code in [404, 500]
                ):
                    logger.info(
                        "Database or container not found. Creating and seeding with sample data...")
                    result = await self._create_database_and_seed()
                    if result["status"] == "healthy":
                        return {
                            "status": "healthy",
                            "database": self.database_name,
                            "message": "Database and container created successfully with sample data",
                        }
                    return result
                raise

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def _create_database_and_seed(self) -> Dict[str, Any]:
        """Create database, container, and seed with sample accessory data."""
        try:
            logger.info(f"Creating database: {self.database_name}")
            database = self.client.create_database_if_not_exists(
                id=self.database_name)

            logger.info(f"Creating container: {self.container_name}")
            database.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400,
            )

            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(
                self.container_name)

            await self._database_seed()
            logger.info("Database setup and seeding completed successfully")
            return {"status": "healthy", "message": "Database and container created successfully with sample data"}
        except Exception as e:
            logger.error(f"Failed to create database and seed data: {e}")
            return {"status": "unhealthy", "error": f"Failed to create database: {e}"}

    async def _database_seed(self) -> None:
        """Seed the existing CosmosDB container with sample accessory data."""
        if self.container is None:
            raise RuntimeError(
                "Cosmos container is not initialized; cannot seed database")

        logger.info("Seeding container with sample accessory data")
        sample_accessories = [
            {
                "id": "x1",
                "name": "Chew Toy",
                "type": "toy",
                "price": 8.99,
                "stock": 12,
                "size": "M",
                "imageUrl": "",
                "description": "Durable rope",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
            },
            {
                "id": "x2",
                "name": "Salmon Treats",
                "type": "food",
                "price": 5.49,
                "stock": 3,
                "size": "S",
                "imageUrl": "",
                "description": "Soft chews",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat(),
            },
        ]

        for accessory_data in sample_accessories:
            try:
                self.container.create_item(body=accessory_data)
                logger.info(
                    f"Seeded accessory: {accessory_data['name']} ({accessory_data['id']})")
            except cosmos_exceptions.CosmosResourceExistsError:
                logger.info(
                    f"Accessory {accessory_data['name']} ({accessory_data['id']}) already exists, skipping")
                continue

    def create_accessory(self, accessory_data: AccessoryCreate) -> Accessory:
        """Create a new accessory in CosmosDB."""
        try:
            self._ensure_initialized()

            accessory = Accessory(
                **accessory_data.model_dump(),
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow(),
            )
            accessory_dict = accessory.model_dump(mode="json")

            response = self.container.create_item(body=accessory_dict)
            logger.info(f"Created accessory: {response['id']}")

            return Accessory(**response)
        except cosmos_exceptions.CosmosResourceExistsError:
            accessory_id = accessory_dict["id"]
            logger.error(f"Accessory with ID {accessory_id} already exists")
            raise ValueError(
                f"Accessory with ID {accessory_id} already exists")
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error creating accessory: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating accessory: {e}")
            raise

    def get_accessory(self, accessory_id: str) -> Optional[Accessory]:
        """Get an accessory by ID."""
        try:
            self._ensure_initialized()
            response = self.container.read_item(
                item=accessory_id, partition_key=accessory_id)
            logger.info(f"Retrieved accessory: {accessory_id}")
            return Accessory(**response)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Accessory not found: {accessory_id}")
            return None
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(
                f"CosmosDB HTTP error getting accessory {accessory_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error getting accessory {accessory_id}: {e}")
            raise

    def update_accessory(self, accessory_id: str, update_data: AccessoryUpdate) -> Optional[Accessory]:
        """Update an accessory by ID."""
        try:
            self._ensure_initialized()
            existing_accessory = self.get_accessory(accessory_id)
            if not existing_accessory:
                return None

            update_dict = update_data.model_dump(exclude_unset=True)
            if not update_dict:
                return existing_accessory

            accessory_dict = existing_accessory.model_dump(mode="json")
            accessory_dict.update(update_dict)
            accessory_dict["updatedAt"] = datetime.utcnow().isoformat()

            response = self.container.replace_item(
                item=accessory_id, body=accessory_dict)
            logger.info(f"Updated accessory: {accessory_id}")

            return Accessory(**response)
        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Accessory not found for update: {accessory_id}")
            return None
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(
                f"CosmosDB HTTP error updating accessory {accessory_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error updating accessory {accessory_id}: {e}")
            raise

    def delete_accessory(self, accessory_id: str) -> bool:
        """Delete an accessory by ID."""
        try:
            self._ensure_initialized()
            self.container.delete_item(
                item=accessory_id, partition_key=accessory_id)
            logger.info(f"Deleted accessory: {accessory_id}")
            return True
        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Accessory not found for deletion: {accessory_id}")
            return False
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(
                f"CosmosDB HTTP error deleting accessory {accessory_id}: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error deleting accessory {accessory_id}: {e}")
            raise

    async def search_accessories(self, filters: AccessorySearchFilters) -> List[Accessory]:
        """Search accessories with filtering support."""
        try:
            self._ensure_initialized()

            query_parts = ["SELECT * FROM c"]
            parameters: List[Dict[str, Any]] = []
            conditions: List[str] = []

            if filters.search:
                conditions.append(
                    "(CONTAINS(c.name, @search) OR CONTAINS(c.description, @search))")
                parameters.append({"name": "@search", "value": filters.search})

            if filters.type:
                conditions.append("c.type = @type")
                parameters.append({"name": "@type", "value": filters.type})

            if filters.lowStockOnly:
                conditions.append("c.stock < 10")

            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            query_parts.append("ORDER BY c.createdAt DESC")
            query_parts.append(
                f"OFFSET {filters.offset} LIMIT {filters.limit}")

            query = " ".join(query_parts)
            logger.debug(
                f"Executing query: {query} with parameters: {parameters}")

            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=filters.limit,
                )
            )

            accessories: List[Accessory] = []
            for item in items:
                try:
                    accessories.append(Accessory(**item))
                except Exception as e:
                    logger.warning(f"Failed to parse accessory item: {e}")
                    continue

            logger.info(f"Search returned {len(accessories)} accessories")
            return accessories
        except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
            # Database or container doesn't exist - check if it's a "not found" type error
            error_message = str(e).lower()
            if "does not exist" in error_message or "notfound" in error_message or (
                hasattr(e, "status_code") and e.status_code in [404, 500]
            ):
                logger.info(
                    "Database or container not found during search. Creating and seeding with sample data...")
                await self._create_database_and_seed()
                # Retry the search after creating the database
                return await self.search_accessories(filters)
            else:
                logger.error(f"CosmosDB HTTP error searching accessories: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error searching accessories: {e}")
            raise

    async def get_all_accessories(self, limit: int = 100, offset: int = 0) -> List[Accessory]:
        """Get all accessories with pagination support."""
        filters = AccessorySearchFilters(limit=limit, offset=offset)
        return await self.search_accessories(filters)


def get_cosmos_service() -> AccessoryCosmosService:
    """Factory function to create and return a CosmosDB service instance."""
    from config import get_settings

    settings = get_settings()
    return AccessoryCosmosService(
        cosmos_endpoint=settings.cosmos_endpoint,
        cosmos_key=settings.cosmos_key,
        database_name=settings.cosmos_database_name,
        container_name=settings.cosmos_container_name,
    )
