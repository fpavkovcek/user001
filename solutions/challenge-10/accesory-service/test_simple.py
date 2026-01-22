from main import app
import os
import pytest
from fastapi.testclient import TestClient

# Set environment variables before importing main
os.environ["COSMOS_ENDPOINT"] = "https://example.documents.azure.com:443/"
os.environ["COSMOS_KEY"] = "fake_key"

# Import app after setting env vars

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["status"] == "healthy"
