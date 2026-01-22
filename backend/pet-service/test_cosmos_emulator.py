#!/usr/bin/env python3
"""Quick test script to verify connection to a local Azure Cosmos DB Emulator.

Usage:
  python test_cosmos_emulator.py

The script will use the emulator defaults unless overridden by environment variables:
  COSMOS_EMULATOR_URL  (default: https://localhost:8081)
  COSMOS_EMULATOR_KEY  (default: emulator master key)
  COSMOS_DB_NAME       (default: cosmicworks)
  COSMOS_CONTAINER     (default: products)

If you hit SSL issues (emulator uses a self-signed cert), either install the emulator certificate
into your OS trust store, or set REQUESTS_CA_BUNDLE to a CA bundle that includes the emulator cert.
As a last resort for local testing only you can set COSMOS_EMULATOR_DISABLE_SSL_VERIFY=1 to skip
SSL verification (not recommended for anything except local debugging).
"""

import os
import sys
import uuid
import traceback

# DEFAULT_URL = "http://localhost:8081" # Use this on local machine with proper cert setup
DEFAULT_URL = "https://localhost:8081" # Use this inside GitHub Codespaces
DEFAULT_KEY = (
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGG"
    "yPMbIZnqyMsEcaGQy67XIw/Jw=="
)


def main():
    try:
        from azure.cosmos import CosmosClient, PartitionKey
    except ImportError:
        print("Missing dependency: azure-cosmos package is not installed.")
        print("Install with: python -m pip install 'azure-cosmos>=4.2.0,<5'")
        return 2

    url = os.environ.get("COSMOS_EMULATOR_URL", DEFAULT_URL)
    key = os.environ.get("COSMOS_EMULATOR_KEY", DEFAULT_KEY)
    db_name = os.environ.get("COSMOS_DB_NAME", "cosmicworks")
    container_name = os.environ.get("COSMOS_CONTAINER", "products")

    # Optional: disable SSL verification for local debugging only
    disable_ssl = os.environ.get("COSMOS_EMULATOR_DISABLE_SSL_VERIFY", "0") in ("1", "true", "True")

    try:
        client_kwargs = {"url": url, "credential": key}

        # The SDK will use normal SSL verification by default. If the user explicitly
        # requested to disable verification for local debugging, we set verify to False
        # via the requests transport adapter used internally by the SDK.
        if disable_ssl:
            # Newer SDKs accept `connection_verify` in the constructor.
            # Use it if supported; otherwise ignore and rely on environment-based workarounds.
            client_kwargs["connection_verify"] = False

        client = CosmosClient(**client_kwargs)

        print(f"Connected to Cosmos endpoint: {url}")

        database = client.create_database_if_not_exists(id=db_name, offer_throughput=400)
        print(f"Using database: {database.id}")

        container = database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/id"),
        )
        print(f"Using container: {container.id}")

        # Create a test item and upsert it
        test_id = str(uuid.uuid4())
        item = {"id": test_id, "name": "Kiama classic surfboard"}

        result = container.upsert_item(item)
        print("Upserted item id:", result.get("id"))

        # Read back the item
        read_back = container.read_item(item=result.get("id"), partition_key=result.get("id"))
        print("Read back item:", read_back)

        print("Cosmos emulator connectivity test passed.")
        return 0

    except Exception as exc:  # broad catch so we can print helpful debugging info
        print("Cosmos emulator connectivity test failed.")
        print("Error type:", type(exc).__name__)
        print("Message:", str(exc))
        # Provide a short hint for common SSL problems
        if "SSL" in str(exc) or "certificate" in str(exc).lower():
            print("Possible SSL verification issue (emulator uses a self-signed certificate).")
            print("Options:")
            print(" - Install the emulator certificate into your OS trust store.")
            print(" - Set REQUESTS_CA_BUNDLE to point to a CA bundle that includes the emulator cert.")
            print(" - For quick local debugging only, set COSMOS_EMULATOR_DISABLE_SSL_VERIFY=1 to skip verification.")

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
