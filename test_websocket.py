import asyncio
import websockets
import json
import requests
import threading
import time

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

async def websocket_client():
    """WebSocket client untuk testing real-time updates"""
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("WebSocket connected!")
            
            # Listen for messages
            while True:
                try:
                    message = await websocket.recv()
                    print(f"WebSocket received: {message}")
                    
                    data = json.loads(message)
                    if data.get("type") == "queue_updated":
                        action = data.get("data", {}).get("action")
                        print(f"Queue action: {action}")
                        
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed")
                    break
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
                    
    except Exception as e:
        print(f"WebSocket connection error: {e}")

def test_api_endpoint(method, endpoint, data=None):
    """Test API endpoint untuk trigger WebSocket updates"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "GET":
            response = requests.get(url)
        
        print(f"API {method} {endpoint}: {response.status_code}")
        if response.status_code < 400:
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text}")
        else:
            print(f"Error: {response.text}")
        
        return response
        
    except Exception as e:
        print(f"API request error: {e}")
        return None

def test_websocket_flow():
    """Test WebSocket real-time updates"""
    
    print("WebSocket Real-Time Updates Test")
    print("=" * 50)
    
    # Start WebSocket client in background
    ws_thread = threading.Thread(target=lambda: asyncio.run(websocket_client()))
    ws_thread.daemon = True
    ws_thread.start()
    
    # Wait for WebSocket connection
    time.sleep(2)
    
    # Test 1: Create periode
    print("\n1. Testing periode creation...")
    periode_data = {
        "name": "WebSocket Test Periode",
        "is_active": True
    }
    periode_response = test_api_endpoint("POST", "/api/periodes", periode_data)
    
    if periode_response and periode_response.status_code == 201:
        periode_id = periode_response.json()["id"]
        print(f"Created periode: {periode_id}")
        
        # Test 2: Create registration (should trigger WebSocket)
        print("\n2. Testing registration creation...")
        reg_data = {
            "name": "WebSocket Test User",
            "kk_number": "1234567890123456",
            "rt_rw": "001:001",
            "periode_id": periode_id
        }
        reg_response = test_api_endpoint("POST", "/api/registrations", reg_data)
        
        if reg_response and reg_response.status_code == 201:
            registration = reg_response.json()
            print(f"Created registration: {registration['referral_code']}")
            
            # Test 3: Queue operations (should trigger WebSocket)
            print("\n3. Testing queue operations...")
            
            # NEXT operation
            print("Testing NEXT operation...")
            next_response = test_api_endpoint("POST", "/api/queue/next")
            
            time.sleep(1)
            
            # PENDING operation
            print("Testing PENDING operation...")
            pending_response = test_api_endpoint("POST", "/api/queue/pending")
            
            time.sleep(1)
            
            # BACK operation (if there's serving)
            print("Testing BACK operation...")
            back_response = test_api_endpoint("POST", "/api/queue/back")
            
            time.sleep(1)
            
            # Test 4: Update registration (should trigger WebSocket)
            print("\n4. Testing registration update...")
            update_data = {
                "status": "served"
            }
            update_response = test_api_endpoint("PATCH", f"/api/registrations/{registration['id']}", update_data)
            
            time.sleep(1)
            
            # Test 5: Activate another periode (should trigger WebSocket)
            print("\n5. Testing periode activation...")
            periode2_data = {
                "name": "Second WebSocket Test",
                "is_active": False
            }
            periode2_response = test_api_endpoint("POST", "/api/periodes", periode2_data)
            
            if periode2_response and periode2_response.status_code == 201:
                periode2_id = periode2_response.json()["id"]
                activate_response = test_api_endpoint("PATCH", f"/api/periodes/{periode2_id}/activate")
    
    print("\n" + "=" * 50)
    print("WebSocket test completed!")
    print("Check WebSocket messages above for real-time updates")
    
    # Keep running for a few more seconds to catch any delayed messages
    time.sleep(3)

if __name__ == "__main__":
    test_websocket_flow()
