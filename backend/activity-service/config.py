"""
Configuration module for Activity Service

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
        self.cosmos_database_name: str = os.getenv("COSMOS_DATABASE_NAME", "activityservice")
        self.cosmos_container_name: str = os.getenv("COSMOS_CONTAINER_NAME", "activities")
        
        # Application Configuration
        self.app_name: str = "Activity Service API"
        self.app_version: str = "1.0.0"
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # Determine if running locally (CosmosDB Emulator) or in Azure
        self.is_local: bool = self._is_local_development()
        
        # Validate required settings
        if not self.cosmos_endpoint:
            raise ValueError("COSMOS_ENDPOINT environment variable is required")
        
        # Key is only required for local development (emulator)
        if self.is_local and not self.cosmos_key:
            raise ValueError("COSMOS_KEY environment variable is required for local development")
    
    def _is_local_development(self) -> bool:
        """
        Detect if running in local development environment
        
        Returns:
            True if running locally (CosmosDB Emulator), False if in Azure
        """
        if not self.cosmos_endpoint:
            return False
        endpoint = self.cosmos_endpoint.lower()
        # Check if endpoint is localhost or emulator
        return "localhost" in endpoint or "127.0.0.1" in endpoint




@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()