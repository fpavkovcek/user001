"""
Configuration module for Discussions Service

Handles environment variables and Azure CosmosDB configuration
following Azure best practices for credential management.
"""

import os
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings and configuration"""

    def __init__(self):
        # CosmosDB Configuration
        self.cosmos_endpoint: str = os.getenv("COSMOS_ENDPOINT", "")
        self.cosmos_key: str = os.getenv("COSMOS_KEY", "")
        self.cosmos_database_name: str = os.getenv(
            "COSMOS_DATABASE_NAME", "discussionsdb")
        
        # Container names for different collections
        self.cosmos_rooms_container: str = os.getenv(
            "COSMOS_ROOMS_CONTAINER", "rooms")
        self.cosmos_messages_container: str = os.getenv(
            "COSMOS_MESSAGES_CONTAINER", "messages")
        self.cosmos_invitations_container: str = os.getenv(
            "COSMOS_INVITATIONS_CONTAINER", "invitations")
        self.cosmos_attachments_container: str = os.getenv(
            "COSMOS_ATTACHMENTS_CONTAINER", "attachments")

        # Application Configuration
        self.app_name: str = "Discussions Service API"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # Mock mode for testing without CosmosDB
        self.use_mock_db: bool = os.getenv("USE_MOCK_DB", "true").lower() == "true"

        # Determine if running locally (CosmosDB Emulator) or in Azure
        self.is_local: bool = self._is_local_development()

    def _is_local_development(self) -> bool:
        """
        Detect if running in local development environment
        
        Returns True if:
        - COSMOS_ENDPOINT contains 'localhost' or local IP
        - Explicit LOCAL_DEV environment variable is set
        """
        if os.getenv("LOCAL_DEV", "").lower() in ("true", "1", "yes"):
            return True
        
        endpoint = self.cosmos_endpoint.lower()
        local_indicators = ["localhost", "127.0.0.1", "host.docker.internal"]
        return any(indicator in endpoint for indicator in local_indicators)

    def validate_cosmos_config(self) -> bool:
        """Validate that CosmosDB configuration is present"""
        if self.use_mock_db:
            return True
        
        if not self.cosmos_endpoint:
            return False
        
        # Key is only required for local development
        if self.is_local and not self.cosmos_key:
            return False
        
        return True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
