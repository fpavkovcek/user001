"""
Azure CosmosDB Service

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
from models import Pet, PetCreate, PetUpdate, PetSearchFilters

# Configure logging
logger = logging.getLogger(__name__)


class CosmosDBService:
    """
    Service class for Azure CosmosDB operations

    Implements Azure best practices:
    - Uses key-based authentication for CosmosDB
    - Implements proper error handling and retry logic
    - Uses connection pooling and proper resource management
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
                options["connection_verify"] = False  # type: ignore[arg-type]
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
                    return {"status": "healthy", "database": self.settings.cosmos_database_name}

                logger.info(
                    "Database is reachable but empty. Seeding with sample data...")
                await self._database_seed()
                return {
                    "status": "healthy",
                    "database": self.settings.cosmos_database_name,
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
        """Seed the existing CosmosDB container with sample pet data."""
        if self.container is None:
            raise RuntimeError(
                "Cosmos container is not initialized; cannot seed database")

        logger.info("Seeding container with sample pet data")
        sample_pets = [
            {
                "id": "p1",
                "name": "Luna",
                "species": "dog",
                "ageYears": 3,
                "health": 82,
                "happiness": 91,
                "energy": 76,
                "avatarUrl": "",
                "notes": "Loves fetch",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            },
            {
                "id": "p2",
                "name": "Milo",
                "species": "cat",
                "ageYears": 2,
                "health": 88,
                "happiness": 73,
                "energy": 65,
                "avatarUrl": "",
                "notes": "Window watcher",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            },
            {
                "id": "p3",
                "name": "Pico",
                "species": "bird",
                "ageYears": 1,
                "health": 75,
                "happiness": 80,
                "energy": 90,
                "avatarUrl": "",
                "notes": "Chirpy",
                "createdAt": datetime.utcnow().isoformat(),
                "updatedAt": datetime.utcnow().isoformat()
            }
        ]

        for pet_data in sample_pets:
            try:
                self.container.create_item(body=pet_data)
                logger.info(
                    f"Seeded pet: {pet_data['name']} ({pet_data['id']})")
            except cosmos_exceptions.CosmosResourceExistsError:
                logger.info(
                    f"Pet {pet_data['name']} ({pet_data['id']}) already exists, skipping")
                continue

    async def clean_database(self) -> Dict[str, Any]:
        """Delete configured CosmosDB database and reset local references."""
        database_id = self.settings.cosmos_database_name

        try:
            # Ensure we have a client without triggering container creation.
            if self.client is None:
                cosmos_client_options = self._build_cosmos_client_options()
                self.client = CosmosClient(**cosmos_client_options)

            try:
                self.client.delete_database(database_id)
                logger.info(
                    f"Deleted CosmosDB database '{database_id}' and all containers")
            except cosmos_exceptions.CosmosResourceNotFoundError:
                logger.info(
                    f"CosmosDB database '{database_id}' does not exist – nothing to delete")
            except cosmos_exceptions.CosmosHttpResponseError as e:
                logger.error(
                    f"CosmosDB HTTP error deleting database '{database_id}': {e}")
                raise

            # Reset internal state so future operations perform a fresh setup.
            self.client = None
            self.database = None
            self.container = None
            self._initialized = False

            return {
                "status": "clean",
                "database": database_id,
                "message": "CosmosDB database deleted; environment reset"
            }

        except Exception as e:
            logger.error(
                f"Failed to clean CosmosDB database '{database_id}': {e}")
            return {
                "status": "error",
                "database": database_id,
                "error": str(e)
            }

    def create_pet(self, pet_data: PetCreate) -> Pet:
        """
        Create a new pet in CosmosDB

        Args:
            pet_data: Pet creation data

        Returns:
            Created Pet object

        Raises:
            CosmosDBError: If creation fails
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()
            # Create Pet object with generated ID and timestamps
            pet = Pet(**pet_data.model_dump())
            pet_dict = pet.model_dump()

            # Convert datetime objects to ISO strings for CosmosDB
            pet_dict['createdAt'] = pet.createdAt.isoformat()
            pet_dict['updatedAt'] = pet.updatedAt.isoformat()

            # Insert into CosmosDB
            response = self.container.create_item(body=pet_dict)
            logger.info(f"Created pet with ID: {pet.id}")

            return Pet(**response)

        except cosmos_exceptions.CosmosResourceExistsError:
            logger.error(f"Pet with ID {pet.id} already exists")
            raise ValueError(f"Pet with ID {pet.id} already exists")
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error creating pet: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating pet: {e}")
            raise

    def get_pet(self, pet_id: str) -> Optional[Pet]:
        """
        Get a pet by ID

        Args:
            pet_id: Pet identifier

        Returns:
            Pet object if found, None otherwise
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()
            response = self.container.read_item(
                item=pet_id, partition_key=pet_id)
            return Pet(**response)

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Pet not found: {pet_id}")
            return None
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error getting pet {pet_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting pet {pet_id}: {e}")
            raise

    def update_pet(self, pet_id: str, update_data: PetUpdate) -> Optional[Pet]:
        """
        Update a pet by ID

        Args:
            pet_id: Pet identifier
            update_data: Pet update data

        Returns:
            Updated Pet object if successful, None if not found
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()
            # Get existing pet
            existing_pet = self.get_pet(pet_id)
            if not existing_pet:
                return None

            # Apply updates
            update_dict = update_data.model_dump(exclude_unset=True)
            if not update_dict:
                return existing_pet  # No changes

            # Update the existing pet data (with JSON serialization)
            pet_dict = existing_pet.model_dump(mode='json')
            pet_dict.update(update_dict)
            pet_dict['updatedAt'] = datetime.utcnow().isoformat()

            # Update in CosmosDB
            response = self.container.replace_item(item=pet_id, body=pet_dict)
            logger.info(f"Updated pet: {pet_id}")

            return Pet(**response)

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Pet not found for update: {pet_id}")
            return None
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error updating pet {pet_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating pet {pet_id}: {e}")
            raise

    def delete_pet(self, pet_id: str) -> bool:
        """
        Delete a pet by ID

        Args:
            pet_id: Pet identifier

        Returns:
            True if deleted, False if not found
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()
            self.container.delete_item(item=pet_id, partition_key=pet_id)
            logger.info(f"Deleted pet: {pet_id}")
            return True

        except cosmos_exceptions.CosmosResourceNotFoundError:
            logger.info(f"Pet not found for deletion: {pet_id}")
            return False
        except cosmos_exceptions.CosmosHttpResponseError as e:
            logger.error(f"CosmosDB HTTP error deleting pet {pet_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error deleting pet {pet_id}: {e}")
            raise

    async def search_pets(self, filters: PetSearchFilters) -> List[Pet]:
        """
        Search pets with filtering support

        Args:
            filters: Search and filter parameters

        Returns:
            List of Pet objects matching the criteria
        """
        try:
            # Ensure client is initialized
            self._ensure_initialized()
            # Build SQL query based on filters
            query_parts = ["SELECT * FROM c"]
            parameters = []
            conditions = []

            # Add search condition (name or notes) - emulator-compatible version
            if filters.search:
                conditions.append(
                    "(CONTAINS(c.name, @search) OR CONTAINS(c.notes, @search))")
                parameters.append({"name": "@search", "value": filters.search})

            # Add species filter
            if filters.species:
                conditions.append("c.species = @species")
                parameters.append(
                    {"name": "@species", "value": filters.species})

            # Add WHERE clause if there are conditions
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            # Add ordering and pagination
            query_parts.append("ORDER BY c.createdAt DESC")
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

            # Convert to Pet objects
            pets = []
            for item in items:
                try:
                    pets.append(Pet(**item))
                except Exception as e:
                    logger.warning(f"Failed to parse pet item: {e}")
                    continue

            logger.info(f"Found {len(pets)} pets matching criteria")
            return pets

        except (cosmos_exceptions.CosmosResourceNotFoundError, cosmos_exceptions.CosmosHttpResponseError) as e:
            # Database or container doesn't exist - check if it's a "not found" type error
            error_message = str(e).lower()
            if "does not exist" in error_message or "notfound" in error_message or e.status_code in [404, 500]:
                logger.info(
                    "Database or container not found during search. Creating and seeding with sample data...")
                await self._create_database_and_seed()
                # Retry the search after creating the database
                return await self.search_pets(filters)
            else:
                logger.error(f"CosmosDB HTTP error searching pets: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error searching pets: {e}")
            raise

    async def get_all_pets(self, limit: int = 100, offset: int = 0) -> List[Pet]:
        """
        Get all pets with pagination

        Args:
            limit: Maximum number of pets to return
            offset: Number of pets to skip

        Returns:
            List of Pet objects
        """
        filters = PetSearchFilters(limit=limit, offset=offset)
        return await self.search_pets(filters)


# Singleton instance
_cosmos_service: Optional[CosmosDBService] = None


def get_cosmos_service() -> CosmosDBService:
    """Get singleton CosmosDB service instance"""
    global _cosmos_service
    if _cosmos_service is None:
        _cosmos_service = CosmosDBService()
    return _cosmos_service
