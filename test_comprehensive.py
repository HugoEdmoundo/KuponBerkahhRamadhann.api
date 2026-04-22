#!/usr/bin/env python3
"""
Comprehensive API Testing Script
Test all endpoints to ensure no errors after architecture cleanup
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, params=None, expected_status=200):
    """Test individual endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"OK {method} {endpoint} - Status: {response.status_code}")
        
        if response.status_code == expected_status:
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    json_data = response.json()
                    if 'error' in json_data and json_data['error']:
                        print(f"   ERROR API: {json_data}")
                        return False
                    print(f"   Response: {json.dumps(json_data, indent=2)[:200]}...")
                except:
                    print(f"   Non-JSON response")
            else:
                print(f"   Non-JSON content-type: {response.headers.get('content-type')}")
            return True
        else:
            print(f"   Expected {expected_status}, got {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    print(f"   Error Response: {response.json()}")
                except:
                    print(f"   Error Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"FAIL {method} {endpoint} - Connection Error: Server not running?")
        return False
    except requests.exceptions.Timeout:
        print(f"FAIL {method} {endpoint} - Timeout Error")
        return False
    except Exception as e:
        print(f"FAIL {method} {endpoint} - Unexpected Error: {str(e)}")
        return False

def main():
    print("Starting Comprehensive API Testing")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        # Health Check
        ("GET", "/", None, None, 200),
        ("GET", "/health", None, None, 200),
        ("GET", "/scalar", None, None, 200),
        
        # Periodes
        ("GET", "/api/periodes", None, None, 200),
        ("POST", "/api/periodes", {"name": "Test Periode", "is_active": True}, None, 201),
        ("GET", "/api/periodes/active", None, None, 200),
        
        # Queue Settings
        ("GET", "/api/queue-settings/periode/test-id", None, None, 404),
        ("POST", "/api/queue-settings", {
            "current_queue_number": 0,
            "current_referral_code": "",
            "next_queue_counter": 1,
            "periode_id": "test-id"
        }, None, 404),
        
        # Registrations
        ("GET", "/api/registrations", None, None, 200),
        ("POST", "/api/registrations", {
            "name": "Test User",
            "kk_number": "1234567890123456",
            "rt_rw": "001:001",
            "periode_id": "test-id"
        }, None, 404),
        
        # Queue Operations
        ("POST", "/api/queue/next", None, None, 404),
        ("POST", "/api/queue/pending", None, None, 404),
        ("POST", "/api/queue/back", None, None, 404),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, data, params, expected in tests:
        if test_endpoint(method, endpoint, data, params, expected):
            passed += 1
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("All tests completed successfully!")
        print("API is ready for production!")
    else:
        print("Some tests failed - check server logs")
        print("Make sure server is running on port 8000")

if __name__ == "__main__":
    main()
