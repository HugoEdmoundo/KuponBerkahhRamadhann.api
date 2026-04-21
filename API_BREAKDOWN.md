# Queue Management API - Professional Documentation

## 🏗️ Project Structure

```
c:\laragon\www\api.queue\
├── main.py (46 lines - optimized entry point)
├── queue.db (SQLite database)
├── requirements.txt (dependencies)
├── README.md (project documentation)
├── API_BREAKDOWN.md (this file)
├── .env.example (environment template)
├── .git/ (version control)
├── alembic/ (database migrations)
├── alembic.ini (migration config)
└── app/ (modular application)
    ├── database.py (81 lines - optimized)
    ├── websocket.py (35 lines - optimized)
    ├── models/ (Pydantic models)
    │   ├── periode.py
    │   ├── warga.py
    │   └── queue_settings.py
    ├── schemas/ (Validation schemas)
    │   ├── periode.py
    │   ├── warga.py
    │   └── queue_settings.py
    └── routers/ (API endpoints)
        ├── periodes.py (6 endpoints)
        ├── registrations.py (5 endpoints)
        ├── queue_settings.py (4 endpoints)
        └── queue_operations.py (4 endpoints)
```

## 🚀 API Endpoints Overview

### **Base URL**: `http://localhost:8000`
### **Documentation**: `http://localhost:8000/scalar`
### **WebSocket**: `ws://localhost:8000/ws`

---

## 📅 Periode Management (`/api/periodes`)

### Get All Periodes
```http
GET /api/periodes
```
**Response:**
```json
[
  {
    "id": "uuid-string",
    "name": "Periode 2024",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00+07:00",
    "updated_at": "2024-01-01T10:00:00+07:00"
  }
]
```

### Get Active Periode
```http
GET /api/periodes/active
```
**Response:**
```json
{
  "message": "Active periode found",
  "data": {
    "id": "uuid-string",
    "name": "Periode 2024",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00+07:00",
    "updated_at": "2024-01-01T10:00:00+07:00"
  }
}
```

### Create Periode
```http
POST /api/periodes
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Periode 2025",
  "is_active": true
}
```
**Response:**
```json
{
  "id": "uuid-string",
  "name": "Periode 2025",
  "is_active": true,
  "created_at": "2024-01-01T10:00:00+07:00",
  "updated_at": "2024-01-01T10:00:00+07:00"
}
```

### Activate Periode
```http
PATCH /api/periodes/{periode_id}/activate
```
**Response:**
```json
{
  "id": "uuid-string",
  "name": "Periode 2025",
  "is_active": true,
  "created_at": "2024-01-01T10:00:00+07:00",
  "updated_at": "2024-01-01T10:00:00+07:00"
}
```

### Update Periode
```http
PATCH /api/periodes/{periode_id}
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Updated Periode 2025",
  "is_active": false
}
```
**Response:**
```json
{
  "id": "uuid-string",
  "name": "Updated Periode 2025",
  "is_active": false,
  "created_at": "2024-01-01T10:00:00+07:00",
  "updated_at": "2024-01-01T10:00:00+07:00"
}
```

### Delete Periode
```http
DELETE /api/periodes/{periode_id}
```
**Response:**
```json
{
  "message": "Periode deleted successfully"
}
```

---

## 👥 Registration Management (`/api/registrations`)

### Get All Registrations
```http
GET /api/registrations?periodeId={periode_id}&status={status}
```
**Query Parameters:**
- `periodeId` (optional): Filter by periode ID
- `status` (optional): Filter by status (`waiting`, `serving`, `served`, `pending`)

**Response:**
```json
[
  {
    "id": "uuid-string",
    "name": "John Doe",
    "kk_number": "1234567890123456",
    "rt_rw": "01:01",
    "referral_code": "ABC123",
    "queue_number": 1,
    "status": "waiting",
    "created_at": "2024-01-01T10:00:00+07:00",
    "updated_at": "2024-01-01T10:00:00+07:00",
    "periode_id": "uuid-string"
  }
]
```

### Get Registration by ID
```http
GET /api/registrations/{registration_id}
```

### Create Registration
```http
POST /api/registrations
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "John Doe",
  "kk_number": "1234567890123456",
  "rt_rw": "01:01",
  "periode_id": "uuid-string"
}
```
**Response:**
```json
{
  "id": "uuid-string",
  "name": "John Doe",
  "kk_number": "1234567890123456",
  "rt_rw": "01:01",
  "referral_code": "ABC123",
  "queue_number": 1,
  "status": "waiting",
  "created_at": "2024-01-01T10:00:00+07:00",
  "updated_at": "2024-01-01T10:00:00+07:00",
  "periode_id": "uuid-string"
}
```

### Update Registration
```http
PATCH /api/registrations/{registration_id}
Content-Type: application/json
```
**Request Body:**
```json
{
  "name": "Updated Name",
  "status": "serving"
}
```

### Delete Registration
```http
DELETE /api/registrations/{registration_id}
```

---

## ⚙️ Queue Settings (`/api/queue-settings`)

### Get All Queue Settings
```http
GET /api/queue-settings
```

### Get Queue Settings by Periode
```http
GET /api/queue-settings/periode/{periode_id}
```

### Create Queue Settings
```http
POST /api/queue-settings
Content-Type: application/json
```
**Request Body:**
```json
{
  "current_queue_number": 0,
  "current_referral_code": "",
  "next_queue_counter": 1,
  "periode_id": "uuid-string"
}
```

---

## 🎯 Queue Operations (`/api/queue`)

### Handle Next Queue
```http
POST /api/queue/next
```
**Response:**
```json
{
  "message": "Next queue processed successfully",
  "current_queue": {
    "id": "uuid-string",
    "name": "Jane Smith",
    "kk_number": "9876543210987654",
    "rt_rw": "02:02",
    "referral_code": "DEF456",
    "queue_number": 6,
    "status": "serving",
    "created_at": "2024-01-01T10:00:00+07:00",
    "updated_at": "2024-01-01T10:00:00+07:00",
    "periode_id": "uuid-string"
  }
}
```

### Handle Pending Queue
```http
POST /api/queue/pending
```

### Handle Back Queue
```http
POST /api/queue/back
```

---

## 🔌 WebSocket Real-time Updates

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

### WebSocket Message Formats

#### Registration Created
```json
{
  "type": "registration_created",
  "data": {
    "id": "uuid-string",
    "name": "John Doe",
    "queue_number": 1,
    "referral_code": "ABC123",
    "status": "waiting",
    "periode_id": "uuid-string"
  }
}
async function registerPerson(data) {
  const response = await fetch(`${API_BASE}/api/registrations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return await response.json();
}
```

### 4. Error Handling
```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Call Failed:', error);
    throw error;
  }
}
```

---

## 📱 Frontend Integration Checklist

### ✅ Required Features
- [x] Connect ke WebSocket untuk realtime updates
- [x] Display queue status (waiting, serving, served, pending)
- [x] Implement queue operations (next, pending, back)
- [x] Registration form dengan validation
- [x] Periode management interface
- [x] Error handling dan user feedback
- [x] Loading states dan spinners
- [x] Responsive design
- [x] Real-time synchronization

### ✅ Data Flow
1. **Initial Load**: GET `/api/periodes/active` untuk current active periode
2. **Realtime**: WebSocket connection untuk live updates
3. **Operations**: POST ke `/api/queue/*` untuk actions
4. **Registration**: POST ke `/api/registrations` untuk new entries
5. **Periode**: GET/POST/PATCH `/api/periodes` untuk management

### ✅ Status Management
- **waiting**: Tampil di list antrian kiri
- **serving**: Tampil di serving card (highlighted)
- **served**: Tampil di list kanan (completed)
- **pending**: Tampil di popup "terlewat"

### ✅ Error Handling
- **Network**: Retry mechanism dengan exponential backoff
- **Validation**: Client-side validation sebelum API call
- **User Feedback**: Toast notifications untuk success/error
- **Fallback**: Local storage untuk offline mode

### 🎯 Current API Endpoints
- **Active**: GET `/api/periodes/active` - Get active periode
- **Queue**: POST `/api/queue/{next|pending|back}` - Queue operations
- **Registration**: GET/POST/PATCH/DELETE `/api/registrations` - Registration management
- **Periode**: GET/POST/PATCH/DELETE `/api/periodes` - Periode management
- **Settings**: GET/POST `/api/queue-settings/periode/{id}` - Queue settings by periode

### 🚀 Production Ready
- **Clean Architecture**: Hanya endpoint yang digunakan
- **Consistent Responses**: Boolean is_active, colon rt_rw format
- **Robust WebSocket**: Reconnection handling dengan logging
- **Proper Error Handling**: HTTP status codes yang tepat
- **Real-time Updates**: WebSocket broadcasts untuk refetch triggers

**API siap digunakan untuk frontend development! 🎉**
