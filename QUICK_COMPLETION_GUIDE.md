# LAZARUS - QUICK COMPLETION GUIDE

## 🎯 GET TO WORKING SYSTEM IN 3 HOURS

This guide provides the fastest path to a working Lazarus dashboard.

---

## PHASE 1: Database Setup (30 min)

### Step 1.1: Create Alembic Configuration

**File:** `backend/alembic.ini`
```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = postgresql://lazarus_user:lazarus_password_change_me@localhost:5432/lazarus

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### Step 1.2: Initialize Alembic

```bash
cd backend
alembic init migrations
```

### Step 1.3: Configure Migrations Environment

**File:** `backend/migrations/env.py`
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.database import Base
from app.models import *  # Import all models

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

### Step 1.4: Create Initial Migration

```bash
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

### Step 1.5: Create Materialized View

```bash
alembic revision -m "Create patient view"
```

**Edit the generated file:**
```python
def upgrade():
    op.execute("""
        CREATE MATERIALIZED VIEW patient_view AS
        SELECT 
            pa.patient_id,
            pa.patient_raw_id,
            pa.parity_flag,
            cd.decoded_name,
            cd.age,
            cd.ward,
            latest_vitals.bpm AS last_bpm,
            latest_vitals.oxygen AS last_oxygen,
            latest_vitals.timestamp AS last_vitals_timestamp,
            latest_vitals.quality_flag,
            COUNT(DISTINCT cp.id) AS prescription_count,
            EXISTS(
                SELECT 1 FROM patient_alerts 
                WHERE patient_alerts.patient_id = pa.patient_id 
                AND status = 'open'
            ) AS has_active_alert
        FROM patient_alias pa
        LEFT JOIN clean_demographics cd ON cd.patient_raw_id = pa.patient_raw_id
        LEFT JOIN LATERAL (
            SELECT bpm, oxygen, timestamp, quality_flag
            FROM clean_telemetry ct
            WHERE ct.patient_raw_id = pa.patient_raw_id
                AND ct.parity_flag = pa.parity_flag
                AND ct.quality_flag = 'good'
            ORDER BY timestamp DESC
            LIMIT 1
        ) latest_vitals ON true
        LEFT JOIN clean_prescriptions cp ON cp.patient_raw_id = pa.patient_raw_id
        GROUP BY pa.patient_id, pa.patient_raw_id, pa.parity_flag, 
                cd.decoded_name, cd.age, cd.ward,
                latest_vitals.bpm, latest_vitals.oxygen, 
                latest_vitals.timestamp, latest_vitals.quality_flag;

        CREATE UNIQUE INDEX idx_patient_view_id ON patient_view(patient_id);
    """)

def downgrade():
    op.execute("DROP MATERIALIZED VIEW IF EXISTS patient_view")
```

```bash
alembic upgrade head
```

---

## PHASE 2: Seed Data (45 min)

### Create Seed Data Generator

**File:** `backend/seed_data/generate_seeds.py`

```python
"""Generate synthetic patient data for testing"""
import csv
import random
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path

from app.services.telemetry_decoder import encode_telemetry
from app.services.cipher import encrypt_medication

fake = Faker()
BASE_DIR = Path(__file__).parent

# Patient data
PATIENTS = 20
COLLIDING_IDS = 5  # Patients that share IDs (distinguished by parity)

# Medication names
MEDICATIONS = [
    "ASPIRIN", "INSULIN", "MORPHINE", "WARFARIN", "LISINOPRIL",
    "METFORMIN", "ATORVASTATIN", "AMLODIPINE", "OMEPRAZOLE", "GABAPENTIN"
]

WARDS = ["ICU-1", "ICU-2", "ICU-3", "Ward-4", "Ward-5", "ER"]

def generate_patients():
    """Generate patient demographics"""
    patients = []
    used_raw_ids = []
    
    for i in range(PATIENTS):
        if i < COLLIDING_IDS * 2:
            # Create colliding IDs (same raw_id, different parity via different vital signs)
            raw_id = f"P{(i // 2) + 1:05d}"
        else:
            raw_id = f"P{i + 1:05d}"
        
        used_raw_ids.append(raw_id)
        
        age = random.randint(18, 85)
        name = fake.name()
        
        # Simple name cipher for demo (just uppercase)
        name_cipher = name.upper().replace(" ", "")
        
        patients.append({
            'patient_raw_id': raw_id,
            'name_cipher': name_cipher,
            'age': age,
            'ward_code': random.choice(WARDS)
        })
    
    # Write CSV
    with open(BASE_DIR / 'patient_demographics.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patient_raw_id', 'name_cipher', 'age', 'ward_code'])
        writer.writeheader()
        writer.writerows(patients)
    
    return patients

def generate_telemetry(patients):
    """Generate telemetry logs"""
    telemetry = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for patient in patients:
        # 1000 samples over 24 hours
        for j in range(1000):
            timestamp = start_time + timedelta(minutes=j * 1.44)  # ~1.44 min intervals
            
            # Determine base BPM based on patient index (for parity consistency)
            patient_idx = int(patient['patient_raw_id'][1:]) - 1
            if patient_idx < COLLIDING_IDS * 2:
                # Colliding IDs - use parity
                if patient_idx % 2 == 0:
                    base_bpm = 70  # Even BPM base
                else:
                    base_bpm = 75  # Odd BPM base
            else:
                base_bpm = random.randint(60, 90)
            
            # Add variation
            bpm = base_bpm + random.randint(-10, 10)
            spo2 = random.randint(94, 100)
            
            # 5% corrupted samples
            if random.random() < 0.05:
                # Corrupt sample
                if random.random() < 0.5:
                    hex_payload = "DEADBEEF"  # Invalid hex
                else:
                    bpm = random.randint(250, 300)  # Out of range
                    hex_payload = encode_telemetry(bpm, spo2)
            else:
                hex_payload = encode_telemetry(bpm, spo2)
            
            telemetry.append({
                'patient_raw_id': patient['patient_raw_id'],
                'timestamp': timestamp.isoformat(),
                'hex_payload': hex_payload,
                'source_device': f"MONITOR_{random.randint(1,10)}"
            })
    
    # Write CSV
    with open(BASE_DIR / 'telemetry_logs.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patient_raw_id', 'timestamp', 'hex_payload', 'source_device'])
        writer.writeheader()
        writer.writerows(telemetry)
    
    return telemetry

def generate_prescriptions(patients):
    """Generate prescriptions"""
    prescriptions = []
    
    for patient in patients:
        num_meds = random.randint(3, 8)
        
        for _ in range(num_meds):
            med_name = random.choice(MEDICATIONS)
            age = patient['age']
            med_cipher = encrypt_medication(med_name, age)
            
            prescriptions.append({
                'patient_raw_id': patient['patient_raw_id'],
                'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'age': age,
                'med_cipher_text': med_cipher,
                'dosage': f"{random.choice([2, 5, 10, 25, 50, 100])}mg",
                'route': random.choice(['PO', 'IV', 'SC', 'IM'])
            })
    
    # Write CSV
    with open(BASE_DIR / 'prescription_audit.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['patient_raw_id', 'timestamp', 'age', 'med_cipher_text', 'dosage', 'route'])
        writer.writeheader()
        writer.writerows(prescriptions)
    
    return prescriptions

if __name__ == "__main__":
    print("Generating seed data...")
    
    patients = generate_patients()
    print(f"✓ Generated {len(patients)} patients")
    
    telemetry = generate_telemetry(patients)
    print(f"✓ Generated {len(telemetry)} telemetry samples")
    
    prescriptions = generate_prescriptions(patients)
    print(f"✓ Generated {len(prescriptions)} prescriptions")
    
    print("\\nSeed data generated successfully!")
    print(f"  - patient_demographics.csv")
    print(f"  - telemetry_logs.csv")
    print(f"  - prescription_audit.csv")
```

### Create Seed Data Loader

**File:** `backend/seed_data/load_seeds.py`

```python
"""Load seed data into database"""
import csv
from pathlib import Path
from datetime import datetime

from app.database import SessionLocal
from app.models.staging import StgPatientDemographics, StgTelemetryLogs, StgPrescriptionAudit
from app.models.cleaned import CleanTelemetry, CleanPrescriptions, CleanDemographics
from app.services.telemetry_decoder import decode_telemetry
from app.services.cipher import decrypt_medication
from app.services.identity_reconciler import reconcile_patient_identity

BASE_DIR = Path(__file__).parent

def load_staging_data():
    """Load CSV files into staging tables"""
    db = SessionLocal()
    
    print("Loading patient demographics...")
    with open(BASE_DIR / 'patient_demographics.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            demo = StgPatientDemographics(**row)
            db.add(demo)
    db.commit()
    print("✓ Loaded patient demographics")
    
    print("Loading telemetry logs...")
    with open(BASE_DIR / 'telemetry_logs.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['timestamp'] = datetime.fromisoformat(row['timestamp'])
            telem = StgTelemetryLogs(**row)
            db.add(telem)
    db.commit()
    print("✓ Loaded telemetry logs")
    
    print("Loading prescriptions...")
    with open(BASE_DIR / 'prescription_audit.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['timestamp'] = datetime.fromisoformat(row['timestamp'])
            row['age'] = int(row['age'])
            presc = StgPrescriptionAudit(**row)
            db.add(presc)
    db.commit()
    print("✓ Loaded prescriptions")
    
    db.close()

def process_telemetry():
    """Process staging telemetry into cleaned table"""
    db = SessionLocal()
    
    print("Processing telemetry...")
    staging = db.query(StgTelemetryLogs).all()
    
    for record in staging:
        decoded = decode_telemetry(record.hex_payload)
        
        clean = CleanTelemetry(
            patient_raw_id=record.patient_raw_id,
            timestamp=record.timestamp,
            hex_payload=record.hex_payload,
            bpm=decoded['bpm'],
            oxygen=decoded['oxygen'],
            parity_flag=decoded['parity_flag'],
            quality_flag=decoded['quality_flag']
        )
        db.add(clean)
    
    db.commit()
    print(f"✓ Processed {len(staging)} telemetry records")
    db.close()

def process_prescriptions():
    """Process staging prescriptions into cleaned table"""
    db = SessionLocal()
    
    print("Processing prescriptions...")
    staging = db.query(StgPrescriptionAudit).all()
    
    for record in staging:
        decoded_name = decrypt_medication(record.med_cipher_text, record.age)
        
        clean = CleanPrescriptions(
            patient_raw_id=record.patient_raw_id,
            age=record.age,
            timestamp=record.timestamp,
            med_cipher_text=record.med_cipher_text,
            med_decoded_name=decoded_name,
            dosage=record.dosage,
            route=record.route
        )
        db.add(clean)
    
    db.commit()
    print(f"✓ Processed {len(staging)} prescriptions")
    db.close()

def process_demographics():
    """Process staging demographics into cleaned table"""
    db = SessionLocal()
    
    print("Processing demographics...")
    staging = db.query(StgPatientDemographics).all()
    
    for record in staging:
        clean = CleanDemographics(
            patient_raw_id=record.patient_raw_id,
            name_cipher=record.name_cipher,
            decoded_name=record.name_cipher,  # Simple decode for demo
            age=record.age,
            ward=record.ward_code
        )
        db.add(clean)
    
    db.commit()
    print(f"✓ Processed {len(staging)} demographics")
    db.close()

def reconcile_identities():
    """Create patient aliases using BPM parity"""
    db = SessionLocal()
    
    print("Reconciling patient identities...")
    demographics = db.query(CleanDemographics).all()
    
    for demo in demographics:
        patient_id = reconcile_patient_identity(demo.patient_raw_id, db)
        print(f"  - {demo.patient_raw_id} → {patient_id}")
    
    print("✓ Identity reconciliation complete")
    db.close()

def refresh_materialized_view():
    """Refresh patient view"""
    db = SessionLocal()
    db.execute("REFRESH MATERIALIZED VIEW patient_view")
    db.commit()
    print("✓ Refreshed materialized view")
    db.close()

if __name__ == "__main__":
    print("=" * 60)
    print(" LAZARUS - Seed Data Loader")
    print("=" * 60)
    print()
    
    load_staging_data()
    process_telemetry()
    process_prescriptions()
    process_demographics()
    reconcile_identities()
    refresh_materialized_view()
    
    print()
    print("✅ Seed data loaded successfully!")
    print()
    print("Next steps:")
    print("  1. Start backend: uvicorn app.main:app --reload")
    print("  2. Visit API docs: http://localhost:8000/docs")
    print("  3. Test endpoint: http://localhost:8000/api/patients")
```

### Run Seed Data Generation & Loading

```bash
# Generate CSV files
python seed_data/generate_seeds.py

# Load into database
python seed_data/load_seeds.py
```

---

## PHASE 3: Verify Backend (15 min)

### Start Backend
```bash
uvicorn app.main:app --reload
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# List patients
curl http://localhost:8000/api/patients

# Get alerts
curl http://localhost:8000/api/alerts
```

### Check API Docs
Visit: http://localhost:8000/docs

---

## PHASE 4: Create Minimal Frontend (2 hours)

*This section would contain the full React frontend code, but due to length constraints, refer to standard React + TypeScript + Vite setup with the components outlined in the plan.*

**Key files needed:**
1. `frontend/package.json` - Dependencies
2. `frontend/src/main.tsx` - Entry point
3. `frontend/src/App.tsx` - Router setup
4. `frontend/src/pages/Dashboard.tsx` - Main UI
5. `frontend/src/components/*.tsx` - UI components

---

## 🎯 SIMPLIFIED PATH

**If you want a working system FAST:**

1. ✅ You already have: All backend code
2. ⏳ Generate and load seed data (30 min)
3. ⏳ Start backend and test APIs (15 min)
4. ⏳ Use Postman/curl to interact with system

**Result:** Fully functional backend with data, accessible via API

**Frontend:** Can be added later or use API directly for now

---

## 📞 NEXT STEPS

You now have:
- ✅ Complete backend implementation
- ✅ All business logic
- ✅ Documentation
- ⏳ Database setup instructions
- ⏳ Seed data generators

**To complete:**
1. Run migration commands (5 min)
2. Generate and load seed data (30 min)
3. Test backend APIs (15 min)
4. Build frontend UI (2-3 hours)

**Total time to working system: ~3-4 hours**

---

**You're almost there!** 🚀
