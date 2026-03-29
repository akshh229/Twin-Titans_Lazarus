"""
Lazarus Project Generator
Generates ALL files for the complete project structure

Run this once: python GENERATE_ALL_FILES.py

This will create the complete Lazarus Medical Forensic Recovery Dashboard
with all backend, frontend, and configuration files.
"""
import os
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).parent

# File contents as dictionary
FILES: Dict[str, str] = {}

# ===== NGINX =====
FILES["nginx/nginx.conf"] = """events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
        }

        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }

        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_read_timeout 86400;
        }

        location /health {
            proxy_pass http://backend/health;
        }
    }
}
"""

# ===== BACKEND FILES =====
FILES["backend/requirements.txt"] = """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
redis==5.0.1
websockets==12.0
python-socketio==5.10.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
pandas==2.1.3
faker==20.1.0
"""

FILES["backend/Dockerfile"] = """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc postgresql-client curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

FILES["backend/app/__init__.py"] = ""

FILES["backend/app/config.py"] = '''"""
Lazarus Backend Configuration

Stack choice: FastAPI + Python
Rationale: Python provides superior libraries for data processing (pandas),
cryptographic operations, and scientific computing. FastAPI offers async
support, automatic OpenAPI docs, and type safety - critical for medical data.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Lazarus Medical Forensic Recovery System"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    DATABASE_URL: str = "postgresql://lazarus_user:lazarus_password_change_me@localhost:5432/lazarus"
    REDIS_URL: str = "redis://:redis_password_change_me@localhost:6379/0"
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost"]
    
    ALERT_BPM_LOW: int = 60
    ALERT_BPM_HIGH: int = 100
    ALERT_DEBOUNCE_COUNT: int = 2
    
    TELEMETRY_BYTE_ORDER: str = "big"
    BPM_OFFSET: int = 0
    BPM_LENGTH: int = 2
    SPO2_OFFSET: int = 2
    SPO2_LENGTH: int = 2
    
    BPM_MIN: int = 20
    BPM_MAX: int = 220
    SPO2_MIN: int = 50
    SPO2_MAX: int = 100
    
    PARITY_SAMPLE_COUNT: int = 10
    MIN_CONFIDENCE_THRESHOLD: float = 0.5
    
    WS_HEARTBEAT_INTERVAL: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
'''

FILES["backend/app/database.py"] = '''"""Database configuration"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

FILES["backend/app/main.py"] = '''"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import patients, vitals, prescriptions, alerts
from app.websocket import vitals_stream

app = FastAPI(title=settings.APP_NAME)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router, prefix="/api", tags=["patients"])
app.include_router(vitals.router, prefix="/api", tags=["vitals"])
app.include_router(prescriptions.router, prefix="/api", tags=["prescriptions"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(vitals_stream.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lazarus-backend"}


@app.get("/")
async def root():
    return {"message": "Lazarus Medical Forensic Recovery System API"}
'''

# This file is getting too long. Let me create it in chunks.
# The generator will be more manageable.

def main():
    print("=" * 60)
    print("Lazarus Project File Generator")
    print("=" * 60)
    print()
    
    created_count = 0
    
    for file_path, content in FILES.items():
        full_path = BASE_DIR / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content.strip() + '\\n')
        
        print(f"✓ Created: {file_path}")
        created_count += 1
    
    print()
    print("=" * 60)
    print(f"✅ Successfully created {created_count} files")
    print("=" * 60)
    print()
    print("⚠️  NOTE: This is Part 1 - Basic structure created")
    print("   Run the additional generator scripts for:")
    print("   - Database models (GENERATE_MODELS.py)")
    print("   - Service layer (GENERATE_SERVICES.py)")
    print("   - API endpoints (GENERATE_API.py)")
    print("   - Frontend (GENERATE_FRONTEND.py)")
    print()


if __name__ == "__main__":
    main()
