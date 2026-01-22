#!/usr/bin/env python3
"""
Pet Service API Testing Script

This script provides comprehensive testing of the Pet Service API endpoints.
It can be used for manual testing, integration testing, or API verification.

Usage:
    python test_api.py [--base-url http://localhost:8000] [--verbose]
"""

import requests
import json
import sys
import argparse
from typing import Dict, Any, Optional
import time


class PetServiceTester:
    """Comprehensive tester for Pet Service API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.session = requests.Session()
        self.created_pets = []  # Track created pets for cleanup
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages if verbose mode is enabled"""
        if self.verbose or level == "ERROR":
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {level}: {message}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        self.log(f"{method} {url}")
        
        try:
            response = self.session.request(method, url, **kwargs)
            self.log(f"Response: {response.status_code}")
            if self.verbose and response.content:
                try:
                    self.log(f"Body: {json.dumps(response.json(), indent=2)}")
                except:
                    self.log(f"Body: {response.text}")
            return response
        except requests.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
    
    def test_health_endpoints(self) -> bool:
        """Test health check endpoints"""
        self.log("Testing health endpoints...")
        
        # Test root endpoint
        try:
            response = self.make_request("GET", "/")
            if response.status_code != 200:
                self.log(f"Root endpoint failed: {response.status_code}", "ERROR")
                return False
            
            data = response.json()
            if "status" not in data or data["status"] != "healthy":
                self.log("Root endpoint doesn't show healthy status", "ERROR")
                return False
                
            self.log("✅ Root endpoint test passed")
        except Exception as e:
            self.log(f"Root endpoint test failed: {e}", "ERROR")
            return False
        
        # Test health endpoint
        try:
            response = self.make_request("GET", "/health")
            if response.status_code not in [200, 503]:  # 503 is acceptable if DB is not available
                self.log(f"Health endpoint failed: {response.status_code}", "ERROR")
                return False
                
            self.log("✅ Health endpoint test passed")
            return True
        except Exception as e:
            self.log(f"Health endpoint test failed: {e}", "ERROR")
            return False
    
    def test_create_pet(self, pet_data: Dict[str, Any]) -> Optional[str]:
        """Test pet creation and return pet ID if successful"""
        self.log("Testing pet creation...")
        
        try:
            response = self.make_request("POST", "/api/pets", json=pet_data)
            if response.status_code != 201:
                self.log(f"Pet creation failed: {response.status_code} - {response.text}", "ERROR")
                return None
            
            created_pet = response.json()
            pet_id = created_pet.get("id")
            
            if not pet_id:
                self.log("Pet creation didn't return ID", "ERROR")
                return None
            
            # Verify pet data
            for key, expected_value in pet_data.items():
                if created_pet.get(key) != expected_value:
                    self.log(f"Pet data mismatch for {key}: expected {expected_value}, got {created_pet.get(key)}", "ERROR")
                    return None
            
            self.created_pets.append(pet_id)
            self.log(f"✅ Pet creation test passed - ID: {pet_id}")
            return pet_id
            
        except Exception as e:
            self.log(f"Pet creation test failed: {e}", "ERROR")
            return None
    
    def test_get_pet(self, pet_id: str) -> bool:
        """Test getting a specific pet"""
        self.log(f"Testing get pet: {pet_id}")
        
        try:
            response = self.make_request("GET", f"/api/pets/{pet_id}")
            if response.status_code != 200:
                self.log(f"Get pet failed: {response.status_code}", "ERROR")
                return False
            
            pet = response.json()
            if pet.get("id") != pet_id:
                self.log("Retrieved pet has wrong ID", "ERROR")
                return False
            
            self.log("✅ Get pet test passed")
            return True
            
        except Exception as e:
            self.log(f"Get pet test failed: {e}", "ERROR")
            return False
    
    def test_update_pet(self, pet_id: str, update_data: Dict[str, Any]) -> bool:
        """Test updating a pet"""
        self.log(f"Testing update pet: {pet_id}")
        
        try:
            response = self.make_request("PATCH", f"/api/pets/{pet_id}", json=update_data)
            if response.status_code != 200:
                self.log(f"Update pet failed: {response.status_code}", "ERROR")
                return False
            
            updated_pet = response.json()
            
            # Verify updates were applied
            for key, expected_value in update_data.items():
                if updated_pet.get(key) != expected_value:
                    self.log(f"Update failed for {key}: expected {expected_value}, got {updated_pet.get(key)}", "ERROR")
                    return False
            
            self.log("✅ Update pet test passed")
            return True
            
        except Exception as e:
            self.log(f"Update pet test failed: {e}", "ERROR")
            return False
    
    def test_search_pets(self, search_params: Dict[str, Any]) -> bool:
        """Test pet search functionality"""
        self.log("Testing pet search...")
        
        try:
            response = self.make_request("GET", "/api/pets", params=search_params)
            if response.status_code != 200:
                self.log(f"Pet search failed: {response.status_code}", "ERROR")
                return False
            
            pets = response.json()
            if not isinstance(pets, list):
                self.log("Pet search didn't return a list", "ERROR")
                return False
            
            self.log(f"✅ Pet search test passed - Found {len(pets)} pets")
            return True
            
        except Exception as e:
            self.log(f"Pet search test failed: {e}", "ERROR")
            return False
    
    def test_delete_pet(self, pet_id: str) -> bool:
        """Test deleting a pet"""
        self.log(f"Testing delete pet: {pet_id}")
        
        try:
            response = self.make_request("DELETE", f"/api/pets/{pet_id}")
            if response.status_code != 204:
                self.log(f"Delete pet failed: {response.status_code}", "ERROR")
                return False
            
            # Verify pet is deleted
            verify_response = self.make_request("GET", f"/api/pets/{pet_id}")
            if verify_response.status_code != 404:
                self.log("Pet still exists after deletion", "ERROR")
                return False
            
            if pet_id in self.created_pets:
                self.created_pets.remove(pet_id)
                
            self.log("✅ Delete pet test passed")
            return True
            
        except Exception as e:
            self.log(f"Delete pet test failed: {e}", "ERROR")
            return False
    
    def test_validation_errors(self) -> bool:
        """Test API validation error handling"""
        self.log("Testing validation errors...")
        
        # Test invalid species
        invalid_pet = {
            "name": "Test Pet",
            "species": "invalid_species",
            "ageYears": 5,
            "health": 100,
            "happiness": 100,
            "energy": 100
        }
        
        try:
            response = self.make_request("POST", "/api/pets", json=invalid_pet)
            if response.status_code != 422:  # Validation error
                self.log(f"Expected validation error but got: {response.status_code}", "ERROR")
                return False
            
            self.log("✅ Validation error test passed")
            return True
            
        except Exception as e:
            self.log(f"Validation error test failed: {e}", "ERROR")
            return False
    
    def test_not_found_errors(self) -> bool:
        """Test 404 error handling"""
        self.log("Testing 404 errors...")
        
        fake_id = "nonexistent-pet-id"
        
        try:
            # Test get non-existent pet
            response = self.make_request("GET", f"/api/pets/{fake_id}")
            if response.status_code != 404:
                self.log(f"Expected 404 but got: {response.status_code}", "ERROR")
                return False
            
            # Test update non-existent pet
            response = self.make_request("PATCH", f"/api/pets/{fake_id}", json={"name": "Updated"})
            if response.status_code != 404:
                self.log(f"Expected 404 for update but got: {response.status_code}", "ERROR")
                return False
            
            # Test delete non-existent pet
            response = self.make_request("DELETE", f"/api/pets/{fake_id}")
            if response.status_code != 404:
                self.log(f"Expected 404 for delete but got: {response.status_code}", "ERROR")
                return False
            
            self.log("✅ 404 error tests passed")
            return True
            
        except Exception as e:
            self.log(f"404 error tests failed: {e}", "ERROR")
            return False
    
    def cleanup(self):
        """Clean up any pets created during testing"""
        self.log("Cleaning up created pets...")
        for pet_id in self.created_pets.copy():
            try:
                self.make_request("DELETE", f"/api/pets/{pet_id}")
                self.log(f"Deleted pet: {pet_id}")
            except:
                self.log(f"Failed to delete pet: {pet_id}", "ERROR")
        
        self.created_pets.clear()
    
    def run_all_tests(self) -> bool:
        """Run comprehensive test suite"""
        print(f"🧪 Starting Pet Service API Tests")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 50)
        
        all_passed = True
        
        # Sample pet data for testing
        test_pet = {
            "name": "Test Luna",
            "species": "dog",
            "ageYears": 3,
            "health": 85,
            "happiness": 90,
            "energy": 75,
            "avatarUrl": "https://example.com/luna.jpg",
            "notes": "Test pet for API validation"
        }
        
        try:
            # Test 1: Health endpoints
            if not self.test_health_endpoints():
                all_passed = False
            
            # Test 2: Create pet
            pet_id = self.test_create_pet(test_pet)
            if not pet_id:
                all_passed = False
                return all_passed
            
            # Test 3: Get pet
            if not self.test_get_pet(pet_id):
                all_passed = False
            
            # Test 4: Update pet
            update_data = {"health": 95, "notes": "Updated test pet"}
            if not self.test_update_pet(pet_id, update_data):
                all_passed = False
            
            # Test 5: Search pets
            search_params = {"search": "Test Luna", "species": "dog", "limit": 10}
            if not self.test_search_pets(search_params):
                all_passed = False
            
            # Test 6: Validation errors
            if not self.test_validation_errors():
                all_passed = False
            
            # Test 7: 404 errors
            if not self.test_not_found_errors():
                all_passed = False
            
            # Test 8: Delete pet
            if not self.test_delete_pet(pet_id):
                all_passed = False
            
        finally:
            # Cleanup
            self.cleanup()
        
        print("=" * 50)
        if all_passed:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed!")
            return False


def main():
    parser = argparse.ArgumentParser(description="Test Pet Service API")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for the Pet Service API")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    tester = PetServiceTester(base_url=args.base_url, verbose=args.verbose)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹  Tests interrupted by user")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()