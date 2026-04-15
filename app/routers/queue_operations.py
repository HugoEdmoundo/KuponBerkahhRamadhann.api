from fastapi import APIRouter, HTTPException
from app.database import get_db, get_active_periode, get_queue_settings, get_current_time
from app.websocket import manager, broadcast_websocket
import json
import uuid

router = APIRouter()

@router.get("/queue/status")
def get_queue_status():
    active_periode = get_active_periode()
    if not active_periode:
        raise HTTPException(status_code=404, detail="No active periode")
    
    periode_id = active_periode["id"]
    settings = get_queue_settings(periode_id)
    
    if not settings:
        settings = {
            "current_queue_number": 0,
            "current_referral_code": "",
            "next_queue_counter": 1
        }
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as count FROM warga WHERE periode_id = ? AND status = 'waiting'", (periode_id,))
    waiting_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM warga WHERE periode_id = ? AND status = 'served'", (periode_id,))
    served_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM warga WHERE periode_id = ? AND status = 'pending'", (periode_id,))
    pending_count = cursor.fetchone()["count"]
    
    conn.close()
    
    # Convert is_active from integer to boolean for consistency
    periode_data = dict(active_periode)
    periode_data["is_active"] = bool(periode_data["is_active"])
    
    return {
        "periode": periode_data,
        "queue_settings": settings,
        "current_serving": dict(current_serving) if current_serving else None,
        "statistics": {
            "waiting": waiting_count,
            "serving": 1 if current_serving else 0,
            "served": served_count,
            "pending": pending_count,
            "total": waiting_count + (1 if current_serving else 0) + served_count + pending_count
        }
    }

@router.post("/queue/next")
def handle_next_queue():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM periodes WHERE is_active = 1")
    active_periode = cursor.fetchone()
    
    if not active_periode:
        conn.close()
        return {"error": "No active periode"}
    
    periode_id = active_periode["id"]
    cursor.execute("SELECT id FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    if current_serving:
        cursor.execute("UPDATE warga SET status = 'served' WHERE id = ?", (current_serving["id"],))
    
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'waiting' ORDER BY queue_number LIMIT 1", (periode_id,))
    first_waiting = cursor.fetchone()
    
    if first_waiting:
        cursor.execute("UPDATE warga SET status = 'serving' WHERE id = ?", (first_waiting["id"],))
        
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = ?, current_referral_code = ?, updated_at = ?
            WHERE periode_id = ?
        ''', (first_waiting["queue_number"], first_waiting["referral_code"], get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        broadcast_websocket(json.dumps({
            "type": "queue_updated",
            "data": {
                "action": "next",
                "current_serving": dict(first_waiting),
                "previous_serving_id": current_serving["id"] if current_serving else None,
                "periode_id": periode_id
            }
        }))
        
        return {
            "message": "Queue advanced successfully",
            "current_serving": dict(first_waiting)
        }
    else:
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = 0, current_referral_code = '', updated_at = ?
            WHERE periode_id = ?
        ''', (get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        broadcast_websocket(json.dumps({
            "type": "queue_updated",
            "data": {
                "action": "reset",
                "current_serving": None,
                "periode_id": periode_id
            }
        }))
        
        return {"message": "No waiting queue found"}

@router.post("/queue/pending")
def handle_pending_queue():
    conn = get_db()
    cursor = conn.cursor()
    
    active_periode = get_active_periode()
    if not active_periode:
        conn.close()
        return {"error": "No active periode found"}
    
    periode_id = active_periode["id"]
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    if not current_serving:
        conn.close()
        return {"error": "No current serving to mark as pending"}
    
    cursor.execute("UPDATE warga SET status = 'pending' WHERE id = ?", (current_serving["id"],))
    
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'waiting' ORDER BY queue_number LIMIT 1", (periode_id,))
    first_waiting = cursor.fetchone()
    
    if first_waiting:
        cursor.execute("UPDATE warga SET status = 'serving' WHERE id = ?", (first_waiting["id"],))
        
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = ?, current_referral_code = ?, updated_at = ?
            WHERE periode_id = ?
        ''', (first_waiting["queue_number"], first_waiting["referral_code"], get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        broadcast_websocket(json.dumps({
            "type": "queue_updated",
            "data": {
                "action": "pending",
                "current_serving": dict(first_waiting),
                "pending": dict(current_serving),
                "periode_id": periode_id
            }
        }))
        
        return {
            "message": "Queue handled pending successfully",
            "current_serving": dict(first_waiting),
            "pending": dict(current_serving)
        }
    else:
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = 0, current_referral_code = '', updated_at = ?
            WHERE periode_id = ?
        ''', (get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        broadcast_websocket(json.dumps({
            "type": "queue_updated",
            "data": {
                "action": "pending_reset",
                "current_serving": None,
                "pending": dict(current_serving),
                "periode_id": periode_id
            }
        }))
        
        return {
            "message": "Current serving marked as pending, no waiting queue",
            "current_serving": None,
            "pending": dict(current_serving)
        }

@router.post("/queue/back")
def handle_back_queue():
    conn = get_db()
    cursor = conn.cursor()
    
    active_periode = get_active_periode()
    if not active_periode:
        conn.close()
        return {"error": "No active periode found"}
    
    periode_id = active_periode["id"]
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    if not current_serving:
        conn.close()
        raise HTTPException(status_code=400, detail="No current serving to go back")
    
    cursor.execute("UPDATE warga SET status = 'waiting' WHERE id = ?", (current_serving["id"],))
    
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'served' ORDER BY queue_number DESC LIMIT 1", (periode_id,))
    last_served = cursor.fetchone()
    
    if last_served:
        cursor.execute("UPDATE warga SET status = 'serving' WHERE id = ?", (last_served["id"],))
        
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = ?, current_referral_code = ?, updated_at = ?
            WHERE periode_id = ?
        ''', (last_served["queue_number"], last_served["referral_code"], get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        broadcast_websocket(json.dumps({
            "type": "queue_updated",
            "data": {
                "action": "back",
                "current_serving": dict(last_served),
                "returned_to_waiting": dict(current_serving),
                "periode_id": periode_id
            }
        }))
        
        return {
            "message": "Queue went back successfully",
            "current_serving": dict(last_served),
            "returned_to_waiting": dict(current_serving)
        }
    else:
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = 0, current_referral_code = '', updated_at = ?
            WHERE periode_id = ?
        ''', (get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        broadcast_websocket(json.dumps({
            "type": "queue_updated",
            "data": {
                "action": "back_reset",
                "current_serving": None,
                "returned_to_waiting": dict(current_serving),
                "periode_id": periode_id
            }
        }))
        
        return {
            "message": "Current serving returned to waiting, no served queue found",
            "current_serving": None,
            "returned_to_waiting": dict(current_serving)
        }
