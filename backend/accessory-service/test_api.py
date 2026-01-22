#!/usr/bin/env python3
"""
Accessory Service API Test Script

This script tests the Accessory Service API endpoints.
Run the service first with: ./start.sh
Then run this script: python test_api.py
"""

import requests
import sys
import json
from typing import Optional

BASE_URL = "http://localhost:8030"

# Test counters
tests_passed = 0
tests_failed = 0


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result with formatting"""
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        print(f"  ✅ {test_name}")
    else:
        tests_failed += 1
        print(f"  ❌ {test_name}")
        if details:
            print(f"     Details: {details}")


def test_root():
    """Test root endpoint"""
    print("\n📍 Testing Root Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        passed = (
            response.status_code == 200 and
            response.json().get("service") == "accessory-service" and
            response.json().get("status") == "running"
        )
        print_result("GET / returns service info", passed, str(response.json()))
    except Exception as e:
        print_result("GET / returns service info", False, str(e))


def test_health():
    """Test health check endpoint"""
    print("\n🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = (
            response.status_code == 200 and
            response.json().get("status") == "healthy"
        )
        print_result("GET /health returns healthy status", passed, str(response.json()))
    except Exception as e:
        print_result("GET /health returns healthy status", False, str(e))


def test_create_accessory() -> Optional[str]:
    """Test creating an accessory"""
    print("\n➕ Testing Create Accessory...")
    try:
        accessory_data = {
            "name": "Test Squeaky Toy",
            "type": "toy",
            "price": 12.99,
            "stock": 50,
            "size": "M",
            "description": "A test toy for API testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/accessories",
            json=accessory_data
        )
        passed = (
            response.status_code == 201 and
            response.json().get("name") == "Test Squeaky Toy" and
            "id" in response.json() and
            "createdAt" in response.json()
        )
        print_result("POST /api/accessories creates accessory", passed, str(response.json()))
        
        if passed:
            return response.json().get("id")
        return None
    except Exception as e:
        print_result("POST /api/accessories creates accessory", False, str(e))
        return None


def test_get_accessory(accessory_id: str):
    """Test getting a specific accessory"""
    print("\n🔍 Testing Get Accessory...")
    try:
        response = requests.get(f"{BASE_URL}/api/accessories/{accessory_id}")
        passed = (
            response.status_code == 200 and
            response.json().get("id") == accessory_id
        )
        print_result(f"GET /api/accessories/{accessory_id} returns accessory", passed)
    except Exception as e:
        print_result(f"GET /api/accessories/{accessory_id} returns accessory", False, str(e))


def test_get_accessory_not_found():
    """Test getting a non-existent accessory"""
    print("\n🔍 Testing Get Non-existent Accessory...")
    try:
        response = requests.get(f"{BASE_URL}/api/accessories/non-existent-id")
        passed = response.status_code == 404
        print_result("GET /api/accessories/non-existent returns 404", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_result("GET /api/accessories/non-existent returns 404", False, str(e))


def test_list_accessories():
    """Test listing accessories"""
    print("\n📋 Testing List Accessories...")
    try:
        response = requests.get(f"{BASE_URL}/api/accessories")
        passed = (
            response.status_code == 200 and
            isinstance(response.json(), list)
        )
        print_result("GET /api/accessories returns list", passed, f"Count: {len(response.json())}")
    except Exception as e:
        print_result("GET /api/accessories returns list", False, str(e))


def test_filter_by_type():
    """Test filtering by type"""
    print("\n🔎 Testing Filter by Type...")
    try:
        response = requests.get(f"{BASE_URL}/api/accessories?type=toy")
        passed = (
            response.status_code == 200 and
            isinstance(response.json(), list) and
            all(item.get("type") == "toy" for item in response.json())
        )
        print_result("GET /api/accessories?type=toy returns only toys", passed, f"Count: {len(response.json())}")
    except Exception as e:
        print_result("GET /api/accessories?type=toy returns only toys", False, str(e))


def test_filter_low_stock():
    """Test filtering low stock items"""
    print("\n📉 Testing Low Stock Filter...")
    try:
        response = requests.get(f"{BASE_URL}/api/accessories?lowStockOnly=true")
        passed = (
            response.status_code == 200 and
            isinstance(response.json(), list) and
            all(item.get("stock", 10) < 10 for item in response.json())
        )
        print_result("GET /api/accessories?lowStockOnly=true returns low stock items", passed, f"Count: {len(response.json())}")
    except Exception as e:
        print_result("GET /api/accessories?lowStockOnly=true returns low stock items", False, str(e))


def test_search():
    """Test search functionality"""
    print("\n🔍 Testing Search...")
    try:
        # First create an item with a unique name
        unique_name = "UniqueSearchTestItem123"
        create_response = requests.post(
            f"{BASE_URL}/api/accessories",
            json={
                "name": unique_name,
                "type": "other",
                "price": 5.99,
                "stock": 10,
                "size": "S"
            }
        )
        
        # Search for it
        response = requests.get(f"{BASE_URL}/api/accessories?search=UniqueSearchTest")
        passed = (
            response.status_code == 200 and
            isinstance(response.json(), list) and
            any(unique_name in item.get("name", "") for item in response.json())
        )
        print_result("GET /api/accessories?search=... finds matching items", passed, f"Count: {len(response.json())}")
        
        # Clean up
        if create_response.status_code == 201:
            item_id = create_response.json().get("id")
            requests.delete(f"{BASE_URL}/api/accessories/{item_id}")
    except Exception as e:
        print_result("GET /api/accessories?search=... finds matching items", False, str(e))


def test_update_accessory(accessory_id: str):
    """Test updating an accessory"""
    print("\n✏️ Testing Update Accessory...")
    try:
        update_data = {
            "stock": 100,
            "description": "Updated description for testing"
        }
        response = requests.patch(
            f"{BASE_URL}/api/accessories/{accessory_id}",
            json=update_data
        )
        passed = (
            response.status_code == 200 and
            response.json().get("stock") == 100 and
            "Updated description" in response.json().get("description", "")
        )
        print_result(f"PATCH /api/accessories/{accessory_id} updates accessory", passed)
    except Exception as e:
        print_result(f"PATCH /api/accessories/{accessory_id} updates accessory", False, str(e))


def test_delete_accessory(accessory_id: str):
    """Test deleting an accessory"""
    print("\n🗑️ Testing Delete Accessory...")
    try:
        response = requests.delete(f"{BASE_URL}/api/accessories/{accessory_id}")
        passed = response.status_code == 204
        print_result(f"DELETE /api/accessories/{accessory_id} deletes accessory", passed, f"Status: {response.status_code}")
        
        # Verify it's gone
        verify_response = requests.get(f"{BASE_URL}/api/accessories/{accessory_id}")
        verify_passed = verify_response.status_code == 404
        print_result("Deleted accessory returns 404 on GET", verify_passed)
    except Exception as e:
        print_result(f"DELETE /api/accessories/{accessory_id} deletes accessory", False, str(e))


def test_validation_invalid_type():
    """Test validation for invalid type"""
    print("\n⚠️ Testing Validation - Invalid Type...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/accessories",
            json={
                "name": "Invalid",
                "type": "furniture",  # Invalid type
                "price": 10.0,
                "stock": 5,
                "size": "M"
            }
        )
        passed = response.status_code == 422
        print_result("POST with invalid type returns 422", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_result("POST with invalid type returns 422", False, str(e))


def test_validation_negative_price():
    """Test validation for negative price"""
    print("\n⚠️ Testing Validation - Negative Price...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/accessories",
            json={
                "name": "Invalid",
                "type": "toy",
                "price": -5.0,  # Negative price
                "stock": 5,
                "size": "M"
            }
        )
        passed = response.status_code == 422
        print_result("POST with negative price returns 422", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_result("POST with negative price returns 422", False, str(e))


def test_validation_missing_fields():
    """Test validation for missing required fields"""
    print("\n⚠️ Testing Validation - Missing Fields...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/accessories",
            json={
                "name": "Incomplete",
                "price": 15.99
                # Missing: type, stock, size
            }
        )
        passed = response.status_code == 422
        print_result("POST with missing fields returns 422", passed, f"Status: {response.status_code}")
    except Exception as e:
        print_result("POST with missing fields returns 422", False, str(e))


def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Accessory Service API Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    
    # Check if service is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to service at", BASE_URL)
        print("   Make sure the service is running: ./start.sh")
        sys.exit(1)
    
    # Run tests
    test_root()
    test_health()
    
    # CRUD tests
    created_id = test_create_accessory()
    if created_id:
        test_get_accessory(created_id)
        test_update_accessory(created_id)
    
    test_get_accessory_not_found()
    test_list_accessories()
    
    # Filter and search tests
    test_filter_by_type()
    test_filter_low_stock()
    test_search()
    
    # Validation tests
    test_validation_invalid_type()
    test_validation_negative_price()
    test_validation_missing_fields()
    
    # Delete test (cleanup)
    if created_id:
        test_delete_accessory(created_id)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"   ✅ Passed: {tests_passed}")
    print(f"   ❌ Failed: {tests_failed}")
    print(f"   📈 Total:  {tests_passed + tests_failed}")
    
    if tests_failed > 0:
        print("\n⚠️  Some tests failed!")
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
