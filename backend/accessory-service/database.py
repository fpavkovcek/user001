"""
Azure CosmosDB Service for Accessory Service

This module provides a service layer for interacting with Azure CosmosDB
following Azure best practices for authentication, error handling, and performance.

Authentication Strategy:
- Local Development (localhost): Uses key-based authentication with emulator
- Azure Deployment: Uses Entra ID (Managed Identity) authentication
"""

import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from azure.cosmos import CosmosClient, exceptions as cosmos_exceptions, PartitionKey
from azure.identity import DefaultAzureCredential

from config import get_settings
from models import Accessory, AccessoryCreate, AccessoryUpdate, AccessorySearchFilters

# Configure logging
logger = logging.getLogger(__name__)

# Low stock threshold
LOW_STOCK_THRESHOLD = 10


class AccessoryCosmosService:
    """
    Service class for Azure CosmosDB operations for Accessories

    Implements Azure best practices:
    - Uses key-based authentication for local, Managed Identity for Azure
    - Implements lazy initialization pattern
    - Implements proper error handling and retry logic
    - Uses dynamic query building without WHERE 1=1 tautologies
    """

    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[CosmosClient] = None
        self.database = None
        self.container = None
        self._initialized = False

    def _build_cosmos_client_options(self) -> Dict[str, Any]:
        """
        Build CosmosClient configuration for consistent usage across services.

        Authentication strategy:
        - Local (localhost): Key-based authentication with optional SSL verification disabled
        - Azure: Entra ID (Managed Identity) authentication via DefaultAzureCredential
        """
        options: Dict[str, Any] = {
            "url": self.settings.cosmos_endpoint,
            "connection_timeout": 30,
            "request_timeout": 30,
        }

        if self.settings.is_local:
            # Local development: Use key-based authentication
            logger.info("Using key-based authentication (local development)")
            options["credential"] = self.settings.cosmos_key

            # Check if SSL verification should be disabled (for emulator)
            disable_ssl_verify = os.getenv(
                "COSMOS_EMULATOR_DISABLE_SSL_VERIFY", "0").lower() in ("1", "true", "yes")

            if disable_ssl_verify:
                options["connection_verify"] = False
                logger.warning(
                    "COSMOS_EMULATOR_DISABLE_SSL_VERIFY is enabled – SSL certificate verification is DISABLED (emulator/dev only)")
        else:
            # Azure deployment: Use Entra ID (Managed Identity) authentication
            logger.info(
                "Using Entra ID authentication (Azure deployment with Managed Identity)")
            credential = DefaultAzureCredential()
            options["credential"] = credential

        return options

    def _ensure_initialized(self):
        """
        Ensure CosmosDB client is initialized (lazy initialization)

        Uses appropriate authentication based on environment:
        - Local: Key-based authentication
        - Azure: Entra ID (Managed Identity) authentication
        """
        if self._initialized:
            return

        try:
            auth_type = "key-based (local)" if self.settings.is_local else "Entra ID (Managed Identity)"
            logger.info(
                f"Initializing CosmosDB connection with {auth_type} authentication")

            cosmos_client_options = self._build_cosmos_client_options()
            endpoint = cosmos_client_options["url"]

            if endpoint.startswith("http://") and not self.settings.is_local:
                logger.warning(
                    "COSMOS_ENDPOINT is using http:// in production – consider switching to https://")

            self.client = CosmosClient(**cosmos_client_options)
            logger.info(f"Connected to CosmosDB endpoint: {endpoint}")

            # Get database and container references
            self.database = self.client.get_database_client(
                self.settings.cosmos_database_name)
            self.container = self.database.get_container_client(
                self.settings.cosmos_container_name)

            self._initialized = True
            logger.info(
                f"Successfully connected to CosmosDB: {self.settings.cosmos_database_name}/{self.settings.cosmos_container_name} using {auth_type}")

        except Exception as e:
            logger.error(f"Failed to initialize CosmosDB client: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Health check for the CosmosDB connection

        If database or container doesn't exist, creates them and seeds with sample data
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
                    return {
                        "status": "healthy",
                        "database": self.settings.cosmos_database_name,
                        "container": self.settings.cosmos_container_name
                    }

                logger.info(
                    "Database is reachable but empty. Seeding with sample data...")
                await self._database_seed()
                return {
                    "status": "healthy",
                    "database": self.settings.cosmos_database_name,
                    "container": self.settings.cosmos_container_name,
                    "message": "Database was empty and has been seeded with sample data"
                }

            except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
                # Database or container doesn't exist - check if it's a "not found" type error
                error_message = str(e).lower()
                if "does not exist" in error_message or "notfound" in error_message or e.status_code in [404, 500]:
                    logger.info(
                        "Database or container not found. Creating and seeding with sample data...")
                    await self._create_database_and_seed()
                    return {
                        "status": "healthy",
                        "database": self.settings.cosmos_database_name,
                        "container": self.settings.cosmos_container_name,
                        "message": "Database and container created successfully with sample data"
                    }
                else:
                    # Re-raise if it's a different type of error
                    raise

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def _create_database_and_seed(self):
        """Create database, container and seed with sample data"""
        try:
            # Create database if it doesn't exist
            logger.info(
                f"Creating database: {self.settings.cosmos_database_name}")
            database = self.client.create_database_if_not_exists(
                id=self.settings.cosmos_database_name
            )

            # Create container if it doesn't exist
            logger.info(
                f"Creating container: {self.settings.cosmos_container_name}")
            container = database.create_container_if_not_exists(
                id=self.settings.cosmos_container_name,
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400  # Minimum RU/s for manual throughput
            )

            # Update our references
            self.database = self.client.get_database_client(
                self.settings.cosmos_database_name)
            self.container = self.database.get_container_client(
                self.settings.cosmos_container_name)

            await self._database_seed()
            logger.info("Database setup and seeding completed successfully")

        except Exception as e:
            logger.error(f"Failed to create database and seed data: {e}")
            raise

    async def _database_seed(self) -> None:
        """Seed the existing CosmosDB container with sample accessory data."""
        if self.container is None:
            raise RuntimeError(
                "Cosmos container is not initialized; cannot seed database")

        logger.info("Seeding container with sample accessory data")
        sample_accessories = [
            {
                "id": "seed-toy-001",
                "name": "Squeaky Ball",
                "type": "toy",
                "description": "A fun squeaky ball for dogs of all sizes",
                "price": 12.99,
                "stock": 50,
                "size": "M",
                "imageUrl": None,
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            },
            {
                "id": "seed-food-001",
                "name": "Premium Dog Food",
                "type": "food",
                "description": "Nutritious dry food for adult dogs",
                "price": 45.99,
                "stock": 5,  # Low stock item
                "size": "L",
                "imageUrl": None,
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
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

    async def search_accessories(self, filters: AccessorySearchFilters) -> List[Accessory]:
        """
        Search and filter accessories with pagination

        Uses dynamic query building WITHOUT WHERE 1=1 tautologies
        (Cosmos DB Emulator doesn't support tautologies)

        Args:
            filters: Search filters including search term, type, lowStockOnly, limit, offset

        Returns:
            List of matching Accessory objects
        """
        try:
            self._ensure_initialized()

            # Build dynamic query using list-building pattern (no WHERE 1=1)
            filter_clauses = []
            parameters = []

            # Text search in name and description
            if filters.search:
                filter_clauses.append(
                    "(CONTAINS(LOWER(c.name), LOWER(@search)) OR CONTAINS(LOWER(c.description), LOWER(@search)))"
                )
                parameters.append({"name": "@search", "value": filters.search})

            # Type filter
            if filters.type:
                filter_clauses.append("c.type = @type")
                parameters.append({"name": "@type", "value": filters.type})

            # Low stock filter
            if filters.lowStockOnly:
                filter_clauses.append(f"c.stock < {LOW_STOCK_THRESHOLD}")

            # Build the query
            if filter_clauses:
                where_clause = " AND ".join(filter_clauses)
                query = f"SELECT * FROM c WHERE {where_clause} ORDER BY c.createdAt DESC OFFSET @offset LIMIT @limit"
            else:
                query = "SELECT * FROM c ORDER BY c.createdAt DESC OFFSET @offset LIMIT @limit"

            # Add pagination parameters
            parameters.append({"name": "@offset", "value": filters.offset})
            parameters.append({"name": "@limit", "value": filters.limit})

            logger.info(f"Executing query: {query} with params: {parameters}")

            # Execute query
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            logger.info(f"Found {len(items)} accessories matching filters")
            return [Accessory(**item) for item in items]

        except Exception as e:
            logger.error(f"Error searching accessories: {e}")
            raise

    def create_accessory(self, accessory_data: AccessoryCreate) -> Accessory:
        """
        Create a new accessory in CosmosDB

        Args:
            accessory_data: Accessory creation data

        Returns:
            Created Accessory object

        Raises:
            ValueError: If accessory with same ID already exists
        """
        try:
            self._ensure_initialized()

            # Create Accessory object with generated ID and timestamps
            accessory = Accessory(**accessory_data.model_dump())
            accessory_dict = accessory.model_dump()

            # Convert datetime objects to ISO strings for CosmosDB
            accessory_dict['createdAt'] = accessory.createdAt.isoformat()
            accessory_dict['updatedAt'] = accessory.updatedAt.isoformat()

            # Insert into CosmosDB
            response = self.container.create_item(body=accessory_dict)
            logger.info(f"Created accessory with ID: {accessory.id}")

            return Accessory(**response)

        except cosmos_exceptions.CosmosResourceExistsError:
            logger.error(f"Accessory with ID {accessory.id} already exists")
            raise ValueError(f"Accessory with ID {accessory.id} already exists")
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error creating accessory: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating accessory: {e}")
            raise

    def get_accessory(self, accessory_id: str) -> Optional[Accessory]:
        """
        Get an accessory by ID

        Args:
            accessory_id: Accessory identifier

        Returns:
            Accessory object if found, None otherwise
        """
        try:
            self._ensure_initialized()

            response = self.container.read_item(
                item=accessory_id,
                partition_key=accessory_id
            )
            logger.info(f"Retrieved accessory: {accessory_id}")
            return Accessory(**response)

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Accessory not found: {accessory_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving accessory {accessory_id}: {e}")
            raise

    def update_accessory(self, accessory_id: str, update_data: AccessoryUpdate) -> Optional[Accessory]:
        """
        Partially update an accessory

        Args:
            accessory_id: Accessory identifier
            update_data: Fields to update

        Returns:
            Updated Accessory object if found, None otherwise
        """
        try:
            self._ensure_initialized()

            # Get existing accessory
            existing = self.get_accessory(accessory_id)
            if not existing:
                return None

            # Merge updates with existing data
            existing_dict = existing.model_dump()
            update_dict = update_data.model_dump(exclude_unset=True)

            for key, value in update_dict.items():
                if value is not None:
                    existing_dict[key] = value

            # Update the timestamp
            existing_dict['updatedAt'] = datetime.utcnow().isoformat()

            # Convert createdAt to string if it's a datetime
            if isinstance(existing_dict.get('createdAt'), datetime):
                existing_dict['createdAt'] = existing_dict['createdAt'].isoformat()

            # Replace item in CosmosDB
            response = self.container.replace_item(
                item=accessory_id,
                body=existing_dict
            )
            logger.info(f"Updated accessory: {accessory_id}")

            return Accessory(**response)

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Accessory not found for update: {accessory_id}")
            return None
        except Exception as e:
            logger.error(f"Error updating accessory {accessory_id}: {e}")
            raise

    def delete_accessory(self, accessory_id: str) -> bool:
        """
        Delete an accessory

        Args:
            accessory_id: Accessory identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            self._ensure_initialized()

            self.container.delete_item(
                item=accessory_id,
                partition_key=accessory_id
            )
            logger.info(f"Deleted accessory: {accessory_id}")
            return True

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Accessory not found for deletion: {accessory_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting accessory {accessory_id}: {e}")
            raise


# Singleton instance
_cosmos_service: Optional[AccessoryCosmosService] = None


def get_cosmos_service() -> AccessoryCosmosService:
    """Get or create the CosmosDB service singleton"""
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = AccessoryCosmosService()
    return _cosmos_service
