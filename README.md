# Queue Management API

API FastAPI untuk sistem antrian yang menggantikan Supabase dengan dokumentasi Scalar.

## Features

- **FastAPI** framework dengan performa tinggi
- **SQLAlchemy** ORM untuk database PostgreSQL
- **Scalar Documentation** UI yang modern dan user-friendly
- **Queue Management** operations (next, pending, back)
- **Real-time Status** tracking
- **Pydantic** validation

## Database Schema

### Tables:
- `periodes` - Management periode antrian
- `warga` - Data pendaftaran antrian
- `queue_settings` - Konfigurasi antrian per periode

## API Endpoints

### Periode Management
- `GET /api/periodes` - List semua periode
- `GET /api/periodes/active` - Get periode aktif
- `POST /api/periodes` - Create periode baru
- `PATCH /api/periodes/{id}/activate` - Activate periode
- `PATCH /api/periodes/{id}` - Update periode
- `DELETE /api/periodes/{id}` - Delete periode

### Registration (Warga)
- `GET /api/registrations` - List registrasi (dengan filter)
- `GET /api/registrations/{id}` - Get detail registrasi
- `POST /api/registrations` - Create registrasi baru
- `PATCH /api/registrations/{id}` - Update registrasi
- `DELETE /api/registrations/{id}` - Delete registrasi

### Queue Settings
- `GET /api/queue-settings` - List semua settings
- `GET /api/queue-settings/periode/{periode_id}` - Get settings periode
- `POST /api/queue-settings` - Create settings
- `PATCH /api/queue-settings/{id}` - Update settings

### Queue Management
- `POST /api/queue/next` - Panggil antrian berikutnya
- `POST /api/queue/pending` - Tunda antrian saat ini
- `POST /api/queue/back` - Kembali ke antrian sebelumnya
- `GET /api/queue/status` - Get status antrian saat ini

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your database configuration
```

3. Run the server:
```bash
python run.py
```

## Documentation

Buka `http://localhost:8000/docs` untuk melihat dokumentasi API dengan Scalar UI.

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `DEBUG` - Debug mode (default: true)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

## Queue Logic

### Next Operation
1. Ubah `serving` saat ini jadi `served`
2. Ubah `waiting[0]` jadi `serving`
3. Update `queue_settings`

### Pending Operation
1. Ubah `serving` saat ini jadi `pending`
2. Panggil `waiting[0]` sebagai `serving`
3. Update `queue_settings`

### Back Operation
1. Ubah `serving` saat ini jadi `waiting`
2. Ambil terakhir `served` jadi `serving`
3. Update `queue_settings`

## Status Flow

```
waiting -> serving -> served
         \-> pending
```

## Development

Server akan otomatis restart saat ada perubahan file (development mode).
