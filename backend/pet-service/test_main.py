"""
Test suite for Pet Service API

Run with: python -m pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import Mock, patch

from main import app
from models import Pet, PetCreate, PetUpdate


client = TestClient(app)


# Mock data
SAMPLE_PET_DATA = {
    "name": "Luna",
    "species": "dog",
    "ageYears": 3,
    "health": 85,
    "happiness": 90,
    "energy": 75,
    "avatarUrl": "https://example.com/luna.jpg",
    "notes": "Friendly golden retriever"
}

SAMPLE_PET_RESPONSE = {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Luna",
    "species": "dog",
    "ageYears": 3,
    "health": 85,
    "happiness": 90,
    "energy": 75,
    "avatarUrl": "https://example.com/luna.jpg",
    "notes": "Friendly golden retriever",
    "createdAt": "2025-01-01T00:00:00",
    "updatedAt": "2025-01-01T00:00:00"
}


@pytest.fixture
def mock_db_service():
    """Mock database service for testing"""
    with patch('main.get_cosmos_service') as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        yield mock_service


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "healthy"

    def test_health_check_success(self, mock_db_service):
        """Test successful health check"""
        mock_db_service.health_check.return_value = {
            "status": "healthy",
            "database": "petservice"
        }
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data

    def test_health_check_failure(self, mock_db_service):
        """Test health check failure"""
        mock_db_service.health_check.side_effect = Exception("DB connection failed")
        
        response = client.get("/health")
        assert response.status_code == 503


class TestPetCRUDOperations:
    """Test pet CRUD operations"""

    def test_create_pet_success(self, mock_db_service):
        """Test successful pet creation"""
        mock_pet = Pet(**SAMPLE_PET_RESPONSE)
        mock_db_service.create_pet.return_value = mock_pet
        
        response = client.post("/api/pets", json=SAMPLE_PET_DATA)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == SAMPLE_PET_DATA["name"]
        assert data["species"] == SAMPLE_PET_DATA["species"]
        assert "id" in data

    def test_create_pet_validation_error(self):
        """Test pet creation with validation error"""
        invalid_data = {**SAMPLE_PET_DATA}
        invalid_data["species"] = "invalid_species"
        
        response = client.post("/api/pets", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_create_pet_missing_required_field(self):
        """Test pet creation with missing required field"""
        invalid_data = {**SAMPLE_PET_DATA}
        del invalid_data["name"]
        
        response = client.post("/api/pets", json=invalid_data)
        assert response.status_code == 422

    def test_get_pet_success(self, mock_db_service):
        """Test successful pet retrieval"""
        mock_pet = Pet(**SAMPLE_PET_RESPONSE)
        mock_db_service.get_pet.return_value = mock_pet
        
        pet_id = SAMPLE_PET_RESPONSE["id"]
        response = client.get(f"/api/pets/{pet_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == pet_id
        assert data["name"] == SAMPLE_PET_RESPONSE["name"]

    def test_get_pet_not_found(self, mock_db_service):
        """Test pet retrieval when pet doesn't exist"""
        mock_db_service.get_pet.return_value = None
        
        response = client.get("/api/pets/nonexistent_id")
        assert response.status_code == 404

    def test_update_pet_success(self, mock_db_service):
        """Test successful pet update"""
        updated_pet_data = {**SAMPLE_PET_RESPONSE, "health": 95}
        mock_pet = Pet(**updated_pet_data)
        mock_db_service.update_pet.return_value = mock_pet
        
        pet_id = SAMPLE_PET_RESPONSE["id"]
        update_data = {"health": 95}
        
        response = client.patch(f"/api/pets/{pet_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["health"] == 95

    def test_update_pet_not_found(self, mock_db_service):
        """Test pet update when pet doesn't exist"""
        mock_db_service.update_pet.return_value = None
        
        update_data = {"health": 95}
        response = client.patch("/api/pets/nonexistent_id", json=update_data)
        assert response.status_code == 404

    def test_delete_pet_success(self, mock_db_service):
        """Test successful pet deletion"""
        mock_db_service.delete_pet.return_value = True
        
        pet_id = SAMPLE_PET_RESPONSE["id"]
        response = client.delete(f"/api/pets/{pet_id}")
        assert response.status_code == 204

    def test_delete_pet_not_found(self, mock_db_service):
        """Test pet deletion when pet doesn't exist"""
        mock_db_service.delete_pet.return_value = False
        
        response = client.delete("/api/pets/nonexistent_id")
        assert response.status_code == 404


class TestPetSearch:
    """Test pet search and filtering"""

    def test_get_pets_no_filters(self, mock_db_service):
        """Test getting all pets without filters"""
        mock_pets = [Pet(**SAMPLE_PET_RESPONSE)]
        mock_db_service.search_pets.return_value = mock_pets
        
        response = client.get("/api/pets")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == SAMPLE_PET_RESPONSE["name"]

    def test_get_pets_with_search(self, mock_db_service):
        """Test getting pets with search term"""
        mock_pets = [Pet(**SAMPLE_PET_RESPONSE)]
        mock_db_service.search_pets.return_value = mock_pets
        
        response = client.get("/api/pets?search=luna")
        assert response.status_code == 200
        
        # Verify the search filter was passed correctly
        mock_db_service.search_pets.assert_called_once()
        call_args = mock_db_service.search_pets.call_args[0][0]
        assert call_args.search == "luna"

    def test_get_pets_with_species_filter(self, mock_db_service):
        """Test getting pets with species filter"""
        mock_pets = [Pet(**SAMPLE_PET_RESPONSE)]
        mock_db_service.search_pets.return_value = mock_pets
        
        response = client.get("/api/pets?species=dog")
        assert response.status_code == 200
        
        # Verify the species filter was passed correctly
        call_args = mock_db_service.search_pets.call_args[0][0]
        assert call_args.species == "dog"

    def test_get_pets_with_pagination(self, mock_db_service):
        """Test getting pets with pagination"""
        mock_pets = [Pet(**SAMPLE_PET_RESPONSE)]
        mock_db_service.search_pets.return_value = mock_pets
        
        response = client.get("/api/pets?limit=10&offset=20")
        assert response.status_code == 200
        
        # Verify pagination parameters
        call_args = mock_db_service.search_pets.call_args[0][0]
        assert call_args.limit == 10
        assert call_args.offset == 20

    def test_get_pets_invalid_species(self):
        """Test getting pets with invalid species filter"""
        response = client.get("/api/pets?species=invalid")
        assert response.status_code == 400

    def test_get_pets_invalid_pagination(self):
        """Test getting pets with invalid pagination parameters"""
        # Test negative offset
        response = client.get("/api/pets?offset=-1")
        assert response.status_code == 422
        
        # Test limit too high
        response = client.get("/api/pets?limit=2000")
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_database_error_handling(self, mock_db_service):
        """Test handling of database errors"""
        mock_db_service.get_pet.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/pets/test_id")
        assert response.status_code == 500
        assert "Failed to retrieve pet" in response.json()["detail"]

    def test_validation_error_handling(self, mock_db_service):
        """Test handling of validation errors"""
        mock_db_service.create_pet.side_effect = ValueError("Invalid pet data")
        
        response = client.post("/api/pets", json=SAMPLE_PET_DATA)
        assert response.status_code == 400
        assert "Invalid pet data" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])