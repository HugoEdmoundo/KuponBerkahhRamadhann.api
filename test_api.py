import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, params=None):
    """Test single endpoint and return response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"\n{'='*50}")
        print(f"TEST: {method} {endpoint}")
        print(f"STATUS: {response.status_code}")
        
        if response.status_code < 400:
            print("SUCCESS ✅")
            try:
                print(f"RESPONSE: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"RESPONSE: {response.text}")
        else:
            print("ERROR ❌")
            print(f"ERROR: {response.text}")
        
        return response
        
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        return None

def test_flow():
    """Test complete flow according to Product Requirements"""
    
    print("🚀 STARTING QUEUE FLOW TEST")
    print("="*60)
    
    # 1. Health Check
    test_endpoint("GET", "/health")
    
    # 2. Get all periodes (should be empty initially)
    test_endpoint("GET", "/api/periodes")
    
    # 3. Create first periode
    periode_data = {
        "name": "Periode Test 2024",
        "is_active": True
    }
    response = test_endpoint("POST", "/api/periodes", data=periode_data)
    
    if response and response.status_code == 201:
        periode_id = response.json()["id"]
        print(f"\n📝 Created periode with ID: {periode_id}")
        
        # 4. Get active periode
        test_endpoint("GET", "/api/periodes/active")
        
        # 5. Check queue settings (should be auto-created)
        settings_response = test_endpoint("GET", f"/api/queue-settings/periode/{periode_id}")
        
        if settings_response and settings_response.status_code == 200:
            settings_data = settings_response.json()
            settings_id = settings_data["id"]
            print(f"\n⚙️ Queue settings found with ID: {settings_id}")
        else:
            print("\n⚠️ Queue settings not found, creating manually...")
            settings_data = {
                "current_queue_number": 0,
                "current_referral_code": "",
                "next_queue_counter": 1,
                "periode_id": periode_id
            }
            settings_response = test_endpoint("POST", "/api/queue-settings", data=settings_data)
            if settings_response and settings_response.status_code == 201:
                settings_id = settings_response.json()["id"]
                print(f"\n⚙️ Created queue settings with ID: {settings_id}")
            
            # 6. Test registration flow (Product Requirements)
            print("\n" + "="*60)
            print("📋 TESTING REGISTRATION FLOW")
            print("="*60)
            
            # Create multiple registrations
            registrations = []
            for i in range(3):
                reg_data = {
                    "name": f"Test User {i+1}",
                    "kk_number": f"123456789012345{i+1}",
                    "rt_rw": f"00{i+1}:00{i+1}",
                    "periode_id": periode_id
                }
                
                reg_response = test_endpoint("POST", "/api/registrations", data=reg_data)
                if reg_response and reg_response.status_code == 201:
                    reg_info = reg_response.json()
                    registrations.append(reg_info)
                    print(f"👤 Registered: {reg_info['name']} - Queue #{reg_info['queue_number']} - Code: {reg_info['referral_code']}")
            
            # 7. Get all registrations
            test_endpoint("GET", "/api/registrations")
            
            # 8. Get queue status
            status_response = test_endpoint("GET", "/api/queue/status")
            
            # 9. Test queue operations
            print("\n" + "="*60)
            print("🔄 TESTING QUEUE OPERATIONS")
            print("="*60)
            
            # Test NEXT operation
            test_endpoint("POST", "/api/queue/next")
            
            # Test NEXT again
            test_endpoint("POST", "/api/queue/next")
            
            # Test PENDING operation
            test_endpoint("POST", "/api/queue/pending")
            
            # Test BACK operation
            test_endpoint("POST", "/api/queue/back")
            
            # 10. Get final queue status
            test_endpoint("GET", "/api/queue/status")
            
            # 11. Test individual registration lookup
            if registrations:
                reg_id = registrations[0]["id"]
                test_endpoint("GET", f"/api/registrations/{reg_id}")
                
                # Test update registration
                update_data = {
                    "status": "served"
                }
                test_endpoint("PATCH", f"/api/registrations/{reg_id}", data=update_data)
            
            # 12. Test queue settings update
            update_settings = {
                "next_queue_counter": 10
            }
            test_endpoint("PATCH", f"/api/queue-settings/{settings_id}", data=update_settings)
            
            # 13. Test periode update
            update_periode = {
                "name": "Updated Periode Name"
            }
            test_endpoint("PATCH", f"/api/periodes/{periode_id}", data=update_periode)
            
            # 14. Test create second periode (to test activation)
            print("\n" + "="*60)
            print("📅 TESTING PERIODE MANAGEMENT")
            print("="*60)
            
            periode2_data = {
                "name": "Periode Test 2025",
                "is_active": False
            }
            periode2_response = test_endpoint("POST", "/api/periodes", data=periode2_data)
            
            if periode2_response and periode2_response.status_code == 201:
                periode2_id = periode2_response.json()["id"]
                
                # Activate second periode
                test_endpoint("PATCH", f"/api/periodes/{periode2_id}/activate")
                
                # Get active periode (should be the new one)
                test_endpoint("GET", "/api/periodes/active")
    
    # 15. Test WebSocket connection (basic check)
    print("\n" + "="*60)
    print("🔌 TESTING WEBSOCKET")
    print("="*60)
    
    try:
        import websocket
        import threading
        
        def on_message(ws, message):
            print(f"📨 WebSocket Message: {message}")
        
        def on_error(ws, error):
            print(f"❌ WebSocket Error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("🔌 WebSocket Closed")
        
        def on_open(ws):
            print("✅ WebSocket Connected")
            # Test by creating a registration after connection
            test_data = {
                "name": "WebSocket Test User",
                "kk_number": "9876543210987654",
                "rt_rw": "999:999",
                "periode_id": periode_id if 'periode_id' in locals() else "test-id"
            }
            test_endpoint("POST", "/api/registrations", data=test_data)
        
        ws_url = "ws://localhost:8000/ws"
        ws = websocket.WebSocketApp(ws_url, 
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
        
        # Run WebSocket in separate thread for 5 seconds
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()
        
        time.sleep(5)
        ws.close()
        
    except ImportError:
        print("⚠️ WebSocket library not installed, skipping WebSocket test")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    print("\n" + "="*60)
    print("🎉 QUEUE FLOW TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    test_flow()
