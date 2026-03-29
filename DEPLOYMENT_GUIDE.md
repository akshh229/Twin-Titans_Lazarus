# Deployment Guide

## Project Lazarus - Medical Forensic Recovery System

---

## Prerequisites

| Requirement | Version | Purpose |
|------------|---------|---------|
| Docker | 24+ | Container orchestration |
| Docker Compose | 2.20+ | Multi-service management |
| Node.js | 20+ | Frontend dev/build |
| Python | 3.11+ | Backend runtime |

---

## Quick Start (Docker)

### 1. Clone & Configure

```bash
cd "E:\Project Lazarus"

# Copy environment template
copy .env.example .env

# Edit .env with secure passwords before production use
```

### 2. Generate Seed Data

```bash
cd backend/seed_data
node generate_seeds.mjs
```

### 3. Launch All Services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **Backend (FastAPI)** on port `8000`
- **Frontend (Vite Dev)** on port `3000`
- **Nginx reverse proxy** on port `80`

### 4. Load Seed Data

In a second terminal:

```bash
docker-compose exec backend python seed_data/load_seeds.py
```

### 5. Start Live Simulator (Optional)

```bash
docker-compose exec backend python app/workers/live_simulator.py
```

### 6. Access the Application

| URL | Description |
|-----|-------------|
| http://localhost | Nginx proxy (full app) |
| http://localhost:3000 | Frontend dev server |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/health | Health check endpoint |

---

## Manual Setup (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Set environment variables
set DATABASE_URL=postgresql://lazarus_user:lazarus_password_change_me@localhost:5432/lazarus
set REDIS_URL=redis://:redis_password_change_me@localhost:6379/0

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` with proxy to backend.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `lazarus` | Database name |
| `POSTGRES_USER` | `lazarus_user` | Database user |
| `POSTGRES_PASSWORD` | `lazarus_password_change_me` | Database password |
| `REDIS_PASSWORD` | `redis_password_change_me` | Redis password |
| `ENVIRONMENT` | `development` | App environment |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed CORS origins |
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL (frontend) |
| `VITE_WS_URL` | `ws://localhost:8000` | WebSocket URL (frontend) |
| `ALERT_BPM_LOW` | `60` | Low BPM alert threshold |
| `ALERT_BPM_HIGH` | `100` | High BPM alert threshold |
| `ALERT_DEBOUNCE_COUNT` | `2` | Consecutive readings before alert |

---

## Production Deployment

### Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Set `ENVIRONMENT=production`
- [ ] Restrict `CORS_ORIGINS` to your domain
- [ ] Enable TLS/SSL via Nginx or a load balancer
- [ ] Use Docker secrets or a vault for credentials
- [ ] Set up database backups (pg_dump cron)
- [ ] Enable Redis persistence (AOF/RDB)

### Frontend Production Build

```bash
cd frontend
npm run build
```

The `dist/` folder contains the static assets. Serve via Nginx or a CDN.

### Nginx TLS Configuration

Add to `nginx.conf`:

```nginx
server {
    listen 443 ssl;
    server_name lazarus.your-hospital.com;

    ssl_certificate     /etc/ssl/certs/lazarus.crt;
    ssl_certificate_key /etc/ssl/private/lazarus.key;

    location / {
        proxy_pass http://frontend;
    }

    location /api/ {
        proxy_pass http://backend;
    }

    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400;
    }
}
```

---

## Database Management

### Run Migrations

```bash
# Via Docker
docker-compose exec backend alembic upgrade head

# Manual
cd backend
alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Seed Data Pipeline

```
generate_seeds.mjs  →  CSV files  →  load_seeds.py  →  staging tables  →  cleaned tables
                                           ↓
                                    reconcile_identities()
                                           ↓
                                    refresh materialized view
```

---

## Running Tests

```bash
# Via Docker
docker-compose exec backend python -m pytest tests/ -v

# Manual
cd backend
python -m pytest tests/ -v --tb=short
```

### Test Coverage

```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## Troubleshooting

### Backend won't connect to database

Ensure PostgreSQL is healthy:

```bash
docker-compose ps
docker-compose logs postgres
```

### Frontend can't reach backend

Check the Vite proxy in `vite.config.ts` and verify backend is running on port 8000.

### Seed data load fails

Ensure CSVs exist in `backend/seed_data/`:

```bash
ls backend/seed_data/*.csv
```

If missing, run `node backend/seed_data/generate_seeds.mjs`.

### WebSocket disconnects

Nginx `proxy_read_timeout` is set to 86400s (24h). For production, adjust based on expected session length.

---

## Service Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│   Browser   │────▶│              Nginx (:80)                 │
└─────────────┘     │  / ──▶ Frontend (:3000)                  │
                    │  /api ──▶ Backend (:8000)                 │
                    │  /ws ──▶ Backend (:8000)                  │
                    └──────────────────────────────────────────┘
                               │              │
                    ┌──────────▼──┐    ┌──────▼───────┐
                    │ PostgreSQL  │    │    Redis      │
                    │   (:5432)   │    │   (:6379)    │
                    └─────────────┘    └──────────────┘
```

---

## Built for St. Jude's Research Hospital
**Project Lazarus - Medical Forensic Recovery System**
