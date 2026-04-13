import sqlite3
import uuid
from datetime import datetime
import random
import string

def get_db_connection():
    conn = sqlite3.connect('queue.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_dummy_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create active periode
    periode_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO periodes (id, name, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (periode_id, "Periode Default", True, now, now))
    
    # Create queue settings
    settings_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO queue_settings (id, current_queue_number, current_referral_code, next_queue_counter, periode_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (settings_id, 0, "", 1, periode_id, now, now))
    
    # Dummy data for 10 people
    dummy_people = [
        {"name": "Budi Santoso", "kk_number": "1234567890123456", "rt_rw": "001/001"},
        {"name": "Siti Nurhaliza", "kk_number": "2345678901234567", "rt_rw": "001/002"},
        {"name": "Ahmad Fauzi", "kk_number": "3456789012345678", "rt_rw": "002/001"},
        {"name": "Dewi Lestari", "kk_number": "4567890123456789", "rt_rw": "002/002"},
        {"name": "Eko Prasetyo", "kk_number": "5678901234567890", "rt_rw": "003/001"},
        {"name": "Fitri Handayani", "kk_number": "6789012345678901", "rt_rw": "003/002"},
        {"name": "Gunawan Wijaya", "kk_number": "7890123456789012", "rt_rw": "004/001"},
        {"name": "Hana Permata", "kk_number": "8901234567890123", "rt_rw": "004/002"},
        {"name": "Irfan Hakim", "kk_number": "9012345678901234", "rt_rw": "005/001"},
        {"name": "Julia Rahmawati", "kk_number": "0123456789012345", "rt_rw": "005/002"}
    ]
    
    for i, person in enumerate(dummy_people, 1):
        referral_code = generate_referral_code()
        
        # Make sure referral code is unique
        cursor.execute("SELECT id FROM warga WHERE referral_code = ?", (referral_code,))
        while cursor.fetchone():
            referral_code = generate_referral_code()
            cursor.execute("SELECT id FROM warga WHERE referral_code = ?", (referral_code,))
        
        person_id = str(uuid.uuid4())
        
        # Set first 3 people as waiting, rest with different statuses
        if i <= 3:
            status = "waiting"
        elif i == 4:
            status = "serving"
        elif i == 5:
            status = "served"
        else:
            status = "pending"
        
        cursor.execute('''
            INSERT INTO warga (id, name, kk_number, rt_rw, referral_code, queue_number, status, created_at, updated_at, periode_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (person_id, person["name"], person["kk_number"], person["rt_rw"], 
              referral_code, i, status, now, now, periode_id))
    
    # Update queue settings to show current serving
    cursor.execute('''
        UPDATE queue_settings 
        SET current_queue_number = 4, current_referral_code = (SELECT referral_code FROM warga WHERE queue_number = 4)
        WHERE periode_id = ?
    ''', (periode_id,))
    
    conn.commit()
    conn.close()
    
    print("Dummy data created successfully!")
    print("Created 10 registrations with different statuses:")
    print("- 3 people waiting")
    print("- 1 person serving (queue #4)")
    print("- 1 person served (queue #5)")  
    print("- 4 people pending")
    print("\nAPI is ready at http://localhost:8000")
    print("Documentation at http://localhost:8000/docs")

if __name__ == "__main__":
    create_dummy_data()
