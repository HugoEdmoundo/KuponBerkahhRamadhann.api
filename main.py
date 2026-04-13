from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference
import sqlite3
import uuid
import random
import string
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="Queue Management API",
    description="Simple API untuk sistem antrian yang menggantikan Supabase",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database helper functions
def get_db():
    """Connect to database"""
    conn = sqlite3.connect('queue.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_database():
    """Create all tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create periodes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS periodes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    # Create warga table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warga (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            kk_number TEXT NOT NULL,
            rt_rw TEXT NOT NULL,
            referral_code TEXT NOT NULL UNIQUE,
            queue_number INTEGER NOT NULL,
            status TEXT DEFAULT 'waiting',
            created_at TEXT,
            updated_at TEXT,
            periode_id TEXT,
            FOREIGN KEY (periode_id) REFERENCES periodes (id)
        )
    ''')
    
    # Create queue_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queue_settings (
            id TEXT PRIMARY KEY,
            current_queue_number INTEGER DEFAULT 0,
            current_referral_code TEXT DEFAULT '',
            next_queue_counter INTEGER DEFAULT 1,
            periode_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (periode_id) REFERENCES periodes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# Scalar documentation endpoint
@app.get("/scalar")
def get_scalar():
    """Scalar API documentation"""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title
    )

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Queue Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
def health():
    return {"status": "healthy"}

# Periode endpoints
@app.get("/api/periodes")
def get_periodes():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM periodes")
    periodes = cursor.fetchall()
    conn.close()
    return [dict(p) for p in periodes]

@app.get("/api/periodes/active")
def get_active_periode():
    """Get currently active periode"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM periodes WHERE is_active = 1")
    periode = cursor.fetchone()
    conn.close()
    return dict(periode) if periode else None

def get_queue_settings(periode_id):
    """Get queue settings for a periode"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queue_settings WHERE periode_id = ?", (periode_id,))
    settings = cursor.fetchone()
    conn.close()
    return dict(settings) if settings else None

def generate_referral_code():
    """Generate random 8-character referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_current_time():
    """Get current time in ISO format"""
    return datetime.now().isoformat()

@app.post("/api/periodes")
def create_periode(data: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # Deactivate all periodes first
    cursor.execute("UPDATE periodes SET is_active = 0")
    
    periode_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO periodes (id, name, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (periode_id, data["name"], data.get("is_active", False), now, now))
    
    conn.commit()
    conn.close()
    
    return {"id": periode_id, "message": "Periode created successfully"}

@app.patch("/api/periodes/{periode_id}/activate")
def activate_periode(periode_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    # Deactivate all periodes
    cursor.execute("UPDATE periodes SET is_active = 0")
    
    # Activate this periode
    cursor.execute("UPDATE periodes SET is_active = 1 WHERE id = ?", (periode_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Periode activated successfully"}

@app.patch("/api/periodes/{periode_id}")
def update_periode(periode_id: str, data: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # If setting this periode to active, deactivate all others
    if data.get("is_active") == True:
        cursor.execute("UPDATE periodes SET is_active = 0")
    
    # Update periode
    update_fields = []
    update_values = []
    
    if "name" in data:
        update_fields.append("name = ?")
        update_values.append(data["name"])
    
    if "is_active" in data:
        update_fields.append("is_active = ?")
        update_values.append(data["is_active"])
    
    if update_fields:
        update_fields.append("updated_at = ?")
        update_values.append(get_current_time())
        update_values.append(periode_id)
        
        query = f"UPDATE periodes SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
    
    conn.commit()
    conn.close()
    
    return {"message": "Periode updated successfully"}

@app.delete("/api/periodes/{periode_id}")
def delete_periode(periode_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM periodes WHERE id = ?", (periode_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Periode deleted successfully"}

# Warga (registrations) endpoints
@app.get("/api/registrations")
def get_registrations(periodeId: str = None, status: str = None):
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM warga WHERE 1=1"
    params = []
    
    if periodeId:
        query += " AND periode_id = ?"
        params.append(periodeId)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY queue_number"
    
    cursor.execute(query, params)
    registrations = cursor.fetchall()
    conn.close()
    return [dict(r) for r in registrations]

@app.post("/api/registrations")
def create_registration(data: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get queue settings for the periode
    cursor.execute("SELECT next_queue_counter FROM queue_settings WHERE periode_id = ?", 
                   (data["periode_id"],))
    settings = cursor.fetchone()
    
    next_queue = settings["next_queue_counter"] if settings else 1
    
    # Generate unique referral code
    import random
    import string
    def generate_referral_code():
        """Generate random 8-character referral code"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def get_current_time():
        """Get current time in ISO format"""
        return datetime.now().isoformat()
    
    referral_code = generate_referral_code()
    
    # Check if referral code exists
    cursor.execute("SELECT id FROM warga WHERE referral_code = ?", (referral_code,))
    while cursor.fetchone():
        referral_code = generate_referral_code()
        cursor.execute("SELECT id FROM warga WHERE referral_code = ?", (referral_code,))
    
    registration_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO warga (id, name, kk_number, rt_rw, referral_code, queue_number, status, created_at, updated_at, periode_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (registration_id, data["name"], data["kk_number"], data["rt_rw"], 
          referral_code, next_queue, "waiting", now, now, data["periode_id"]))
    
    # Update queue settings
    if settings:
        cursor.execute("UPDATE queue_settings SET next_queue_counter = ? WHERE periode_id = ?", 
                       (next_queue + 1, data["periode_id"]))
    else:
        settings_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO queue_settings (id, current_queue_number, current_referral_code, next_queue_counter, periode_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (settings_id, 0, "", next_queue + 1, data["periode_id"], now, now))
    
    conn.commit()
    conn.close()
    
    return {
        "id": registration_id,
        "queue_number": next_queue,
        "referral_code": referral_code,
        "message": "Registration created successfully"
    }

@app.get("/api/registrations/{registration_id}")
def get_registration(registration_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM warga WHERE id = ?", (registration_id,))
    registration = cursor.fetchone()
    conn.close()
    
    if registration:
        return dict(registration)
    else:
        return {"error": "Registration not found"}

@app.patch("/api/registrations/{registration_id}")
def update_registration(registration_id: str, data: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if registration exists
    cursor.execute("SELECT id FROM warga WHERE id = ?", (registration_id,))
    if not cursor.fetchone():
        conn.close()
        return {"error": "Registration not found"}
    
    # Update fields
    update_fields = []
    update_values = []
    
    if "name" in data:
        update_fields.append("name = ?")
        update_values.append(data["name"])
    
    if "kk_number" in data:
        update_fields.append("kk_number = ?")
        update_values.append(data["kk_number"])
    
    if "rt_rw" in data:
        update_fields.append("rt_rw = ?")
        update_values.append(data["rt_rw"])
    
    if "status" in data:
        if data["status"] not in ['waiting', 'serving', 'served', 'pending']:
            conn.close()
            return {"error": "Invalid status"}
        update_fields.append("status = ?")
        update_values.append(data["status"])
    
    if update_fields:
        update_fields.append("updated_at = ?")
        update_values.append(get_current_time())
        update_values.append(registration_id)
        
        query = f"UPDATE warga SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
    
    conn.commit()
    conn.close()
    
    return {"message": "Registration updated successfully"}

@app.delete("/api/registrations/{registration_id}")
def delete_registration(registration_id: str):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM warga WHERE id = ?", (registration_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "Registration deleted successfully"}

# Queue management endpoints
@app.post("/api/queue/next")
def handle_next_queue():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active periode
    cursor.execute("SELECT id FROM periodes WHERE is_active = 1")
    active_periode = cursor.fetchone()
    
    if not active_periode:
        conn.close()
        return {"error": "No active periode"}
    
    periode_id = active_periode["id"]
    
    # Find current serving
    cursor.execute("SELECT id FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    # Mark current serving as served
    if current_serving:
        cursor.execute("UPDATE warga SET status = 'served' WHERE id = ?", (current_serving["id"],))
    
    # Find first waiting
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'waiting' ORDER BY queue_number LIMIT 1", 
                   (periode_id,))
    first_waiting = cursor.fetchone()
    
    if first_waiting:
        # Mark as serving
        cursor.execute("UPDATE warga SET status = 'serving' WHERE id = ?", (first_waiting["id"],))
        
        # Update queue settings
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = ?, current_referral_code = ? 
            WHERE periode_id = ?
        ''', (first_waiting["queue_number"], first_waiting["referral_code"], periode_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Queue advanced successfully",
            "current_serving": dict(first_waiting)
        }
    else:
        # Reset current serving
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = 0, current_referral_code = '' 
            WHERE periode_id = ?
        ''', (periode_id,))
        
        conn.commit()
        conn.close()
        
        return {"message": "No waiting queue found"}

@app.post("/api/queue/pending")
def handle_pending_queue():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active periode
    active_periode = get_active_periode()
    if not active_periode:
        conn.close()
        return {"error": "No active periode found"}
    
    periode_id = active_periode["id"]
    
    # Find current serving
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    if not current_serving:
        conn.close()
        return {"error": "No current serving to mark as pending"}
    
    # Mark current serving as pending
    cursor.execute("UPDATE warga SET status = 'pending' WHERE id = ?", (current_serving["id"],))
    
    # Find first waiting
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'waiting' ORDER BY queue_number LIMIT 1", 
                   (periode_id,))
    first_waiting = cursor.fetchone()
    
    if first_waiting:
        # Mark as serving
        cursor.execute("UPDATE warga SET status = 'serving' WHERE id = ?", (first_waiting["id"],))
        
        # Update queue settings
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = ?, current_referral_code = ?, updated_at = ?
            WHERE periode_id = ?
        ''', (first_waiting["queue_number"], first_waiting["referral_code"], get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Queue handled pending successfully",
            "current_serving": dict(first_waiting),
            "pending": dict(current_serving)
        }
    else:
        # No waiting queue, reset current serving
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = 0, current_referral_code = '', updated_at = ?
            WHERE periode_id = ?
        ''', (get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Current serving marked as pending, no waiting queue",
            "current_serving": None,
            "pending": dict(current_serving)
        }

@app.post("/api/queue/back")
def handle_back_queue():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active periode
    active_periode = get_active_periode()
    if not active_periode:
        conn.close()
        return {"error": "No active periode found"}
    
    periode_id = active_periode["id"]
    
    # Find current serving
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    if not current_serving:
        conn.close()
        return {"error": "No current serving to go back"}
    
    # Mark current serving as waiting
    cursor.execute("UPDATE warga SET status = 'waiting' WHERE id = ?", (current_serving["id"],))
    
    # Find last served
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'served' ORDER BY queue_number DESC LIMIT 1", 
                   (periode_id,))
    last_served = cursor.fetchone()
    
    if last_served:
        # Mark as serving
        cursor.execute("UPDATE warga SET status = 'serving' WHERE id = ?", (last_served["id"],))
        
        # Update queue settings
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = ?, current_referral_code = ?, updated_at = ?
            WHERE periode_id = ?
        ''', (last_served["queue_number"], last_served["referral_code"], get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Queue went back successfully",
            "current_serving": dict(last_served),
            "returned_to_waiting": dict(current_serving)
        }
    else:
        # No served queue, reset current serving
        cursor.execute('''
            UPDATE queue_settings 
            SET current_queue_number = 0, current_referral_code = '', updated_at = ?
            WHERE periode_id = ?
        ''', (get_current_time(), periode_id))
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Current serving returned to waiting, no served queue found",
            "current_serving": None,
            "returned_to_waiting": dict(current_serving)
        }

# Queue settings endpoints
@app.get("/api/queue-settings")
def get_all_queue_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queue_settings")
    settings = cursor.fetchall()
    conn.close()
    
    result = []
    for setting in settings:
        result.append(dict(setting))
    
    return result

@app.get("/api/queue-settings/periode/{periode_id}")
def get_queue_settings_by_periode(periode_id: str):
    settings = get_queue_settings(periode_id)
    
    if settings:
        return dict(settings)
    else:
        return {"error": "Queue settings not found for this periode"}

@app.post("/api/queue-settings")
def create_queue_settings(data: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if periode exists
    cursor.execute("SELECT id FROM periodes WHERE id = ?", (data["periode_id"],))
    if not cursor.fetchone():
        conn.close()
        return {"error": "Periode not found"}
    
    # Check if settings already exist
    existing = get_queue_settings(data["periode_id"])
    if existing:
        conn.close()
        return {"error": "Queue settings already exist for this periode"}
    
    # Create new settings
    settings_id = str(uuid.uuid4())
    now = get_current_time()
    
    cursor.execute('''
        INSERT INTO queue_settings (id, current_queue_number, current_referral_code, next_queue_counter, periode_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (settings_id, 
          data.get("current_queue_number", 0),
          data.get("current_referral_code", ""),
          data.get("next_queue_counter", 1),
          data["periode_id"], now, now))
    
    conn.commit()
    conn.close()
    
    return {
        "id": settings_id,
        "message": "Queue settings created successfully"
    }

@app.patch("/api/queue-settings/{settings_id}")
def update_queue_settings(settings_id: str, data: dict):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if settings exist
    cursor.execute("SELECT id FROM queue_settings WHERE id = ?", (settings_id,))
    if not cursor.fetchone():
        conn.close()
        return {"error": "Queue settings not found"}
    
    # Update fields
    update_fields = []
    update_values = []
    
    if "current_queue_number" in data:
        update_fields.append("current_queue_number = ?")
        update_values.append(data["current_queue_number"])
    
    if "current_referral_code" in data:
        update_fields.append("current_referral_code = ?")
        update_values.append(data["current_referral_code"])
    
    if "next_queue_counter" in data:
        update_fields.append("next_queue_counter = ?")
        update_values.append(data["next_queue_counter"])
    
    if update_fields:
        update_fields.append("updated_at = ?")
        update_values.append(get_current_time())
        update_values.append(settings_id)
        
        query = f"UPDATE queue_settings SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(query, update_values)
    
    conn.commit()
    conn.close()
    
    return {"message": "Queue settings updated successfully"}

@app.get("/api/queue/status")
def get_queue_status():
    conn = get_db()
    cursor = conn.cursor()
    
    # Get active periode
    cursor.execute("SELECT * FROM periodes WHERE is_active = 1")
    active_periode = cursor.fetchone()
    
    if not active_periode:
        conn.close()
        return {"error": "No active periode"}
    
    periode_id = active_periode["id"]
    
    # Get queue settings
    cursor.execute("SELECT * FROM queue_settings WHERE periode_id = ?", (periode_id,))
    settings = cursor.fetchone()
    
    if not settings:
        settings = {
            "current_queue_number": 0,
            "current_referral_code": "",
            "next_queue_counter": 1
        }
    else:
        settings = dict(settings)
    
    # Get current serving
    cursor.execute("SELECT * FROM warga WHERE periode_id = ? AND status = 'serving'", (periode_id,))
    current_serving = cursor.fetchone()
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as count FROM warga WHERE periode_id = ? AND status = 'waiting'", (periode_id,))
    waiting_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM warga WHERE periode_id = ? AND status = 'served'", (periode_id,))
    served_count = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM warga WHERE periode_id = ? AND status = 'pending'", (periode_id,))
    pending_count = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "periode": dict(active_periode),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
