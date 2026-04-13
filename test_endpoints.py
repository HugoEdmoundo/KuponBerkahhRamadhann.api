# Test all endpoints to ensure they work properly
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test an endpoint and return the result"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        elif method == "PATCH":
            response = requests.patch(f"{BASE_URL}{endpoint}", json=data)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}")
        
        print(f"{method} {endpoint} - Status: {response.status_code}")
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"  Response: {json.dumps(result, indent=2)[:200]}...")
                return result
            except:
                print(f"  Response: {response.text[:200]}...")
                return response.text
        else:
            print(f"  Error: {response.text}")
            return None
    except Exception as e:
        print(f"  Exception: {str(e)}")
        return None

def main():
    print("Testing all API endpoints...")
    print("="*50)
    
    # Test basic endpoints
    print("\n1. Basic Endpoints:")
    test_endpoint("GET", "/")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/scalar")
    
    # Test periode endpoints
    print("\n2. Periode Endpoints:")
    periodes = test_endpoint("GET", "/api/periodes")
    active_periode = test_endpoint("GET", "/api/periodes/active")
    
    # Create a new periode
    new_periode = test_endpoint("POST", "/api/periodes", {
        "name": "Test Periode",
        "is_active": False
    })
    
    if new_periode and "id" in new_periode:
        periode_id = new_periode["id"]
        print(f"  Created periode with ID: {periode_id}")
        
        # Test activate periode
        test_endpoint("PATCH", f"/api/periodes/{periode_id}/activate")
        
        # Test update periode
        test_endpoint("PATCH", f"/api/periodes/{periode_id}", {
            "name": "Updated Test Periode"
        })
        
        # Test delete periode
        test_endpoint("DELETE", f"/api/periodes/{periode_id}")
    
    # Get active periode for registration tests
    active_periode = test_endpoint("GET", "/api/periodes/active")
    if active_periode and "id" in active_periode:
        periode_id = active_periode["id"]
        print(f"  Using active periode: {periode_id}")
        
        # Test registration endpoints
        print("\n3. Registration Endpoints:")
        registrations = test_endpoint("GET", "/api/registrations", params={"periodeId": periode_id})
        
        # Create a new registration
        new_registration = test_endpoint("POST", "/api/registrations", {
            "name": "Test User",
            "kk_number": "1234567890123456",
            "rt_rw": "001/001",
            "periode_id": periode_id
        })
        
        if new_registration and "id" in new_registration:
            registration_id = new_registration["id"]
            print(f"  Created registration with ID: {registration_id}")
            
            # Test get specific registration
            test_endpoint("GET", f"/api/registrations/{registration_id}")
            
            # Test update registration
            test_endpoint("PATCH", f"/api/registrations/{registration_id}", {
                "name": "Updated Test User"
            })
            
            # Test delete registration
            test_endpoint("DELETE", f"/api/registrations/{registration_id}")
    
    # Test queue settings endpoints
    print("\n4. Queue Settings Endpoints:")
    queue_settings = test_endpoint("GET", "/api/queue-settings")
    
    if active_periode and "id" in active_periode:
        periode_id = active_periode["id"]
        
        # Test get queue settings by periode
        settings_by_periode = test_endpoint("GET", f"/api/queue-settings/periode/{periode_id}")
        
        # Create queue settings if not exists
        if not settings_by_periode or "error" in settings_by_periode:
            new_settings = test_endpoint("POST", "/api/queue-settings", {
                "current_queue_number": 0,
                "current_referral_code": "",
                "next_queue_counter": 1,
                "periode_id": periode_id
            })
            
            if new_settings and "id" in new_settings:
                settings_id = new_settings["id"]
                print(f"  Created queue settings with ID: {settings_id}")
                
                # Test update queue settings
                test_endpoint("PATCH", f"/api/queue-settings/{settings_id}", {
                    "current_queue_number": 5,
                    "next_queue_counter": 10
                })
    
    # Test queue management endpoints
    print("\n5. Queue Management Endpoints:")
    queue_status = test_endpoint("GET", "/api/queue/status")
    
    # Test queue operations
    test_endpoint("POST", "/api/queue/next")
    test_endpoint("POST", "/api/queue/pending")
    test_endpoint("POST", "/api/queue/back")
    
    # Final status check
    print("\n6. Final Status Check:")
    test_endpoint("GET", "/api/queue/status")
    
    print("\n" + "="*50)
    print("Endpoint testing completed!")

if __name__ == "__main__":
    main()
