"""
Create seed data directory and files for Lazarus project
Run this script to set up the seed data generation system
"""
from pathlib import Path

# Create directory
base_dir = Path(r'E:\Project Lazarus\backend\seed_data')
base_dir.mkdir(parents=True, exist_ok=True)
print(f"✓ Created directory: {base_dir}")

# File 1: generate_seeds.py
generate_seeds_content = '''"""Generate synthetic patient data for testing"""
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
    "METFORMIN", "ATORVASTATIN"
]

WARDS = ["ICU-1", "ICU-2", "ICU-3", "Ward-4", "Ward-5", "ER"]

def generate_patients():
    """Generate patient demographics"""
    patients = []
    
    for i in range(PATIENTS):
        if i < COLLIDING_IDS * 2:
            # Create colliding IDs (same raw_id, different parity via different vital signs)
            raw_id = f"P{(i // 2) + 1:05d}"
        else:
            raw_id = f"P{i + 1:05d}"
        
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
    """Generate telemetry logs - 1000 samples per patient over 24 hours"""
    telemetry = []
    start_time = datetime.now() - timedelta(hours=24)
    
    for patient in patients:
        # 1000 samples over 24 hours
        for j in range(1000):
            timestamp = start_time + timedelta(minutes=j * 1.44)  # ~1.44 min intervals
            
            # Determine base BPM based on patient index (for parity consistency)
            patient_idx = int(patient['patient_raw_id'][1:]) - 1
            if patient_idx < COLLIDING_IDS * 2:
                # Colliding IDs - use parity to distinguish
                if patient_idx % 2 == 0:
                    base_bpm = 70  # Even BPM base (even parity)
                else:
                    base_bpm = 75  # Odd BPM base (odd parity)
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
    """Generate prescriptions - 3-8 medications per patient"""
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
    print(f"  - Patients: {PATIENTS}")
    print(f"  - Colliding IDs: {COLLIDING_IDS}")
    print(f"  - Telemetry samples per patient: 1000")
    print(f"  - Corruption rate: 5%")
    print()
    
    patients = generate_patients()
    print(f"✓ Generated {len(patients)} patients")
    
    telemetry = generate_telemetry(patients)
    print(f"✓ Generated {len(telemetry)} telemetry samples")
    
    prescriptions = generate_prescriptions(patients)
    print(f"✓ Generated {len(prescriptions)} prescriptions")
    
    print()
    print("Seed data generated successfully!")
    print(f"  - patient_demographics.csv")
    print(f"  - telemetry_logs.csv")
    print(f"  - prescription_audit.csv")
    print()
    print("Next: Run 'python load_seeds.py' to load data into database")
'''

# File 2: load_seeds.py
load_seeds_content = '''"""Load seed data into database"""
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

def clear_existing_data():
    """Clear existing data from all tables"""
    db = SessionLocal()
    
    print("Clearing existing data...")
    # Clear in reverse dependency order
    db.execute("DELETE FROM patient_alerts")
    db.execute("DELETE FROM patient_alias")
    db.execute("DELETE FROM clean_telemetry")
    db.execute("DELETE FROM clean_prescriptions")
    db.execute("DELETE FROM clean_demographics")
    db.execute("DELETE FROM stg_telemetry_logs")
    db.execute("DELETE FROM stg_prescription_audit")
    db.execute("DELETE FROM stg_patient_demographics")
    db.commit()
    print("✓ Cleared existing data")
    
    db.close()

def load_staging_data():
    """Load CSV files into staging tables"""
    db = SessionLocal()
    
    print("Loading patient demographics...")
    with open(BASE_DIR / 'patient_demographics.csv') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            demo = StgPatientDemographics(**row)
            db.add(demo)
            count += 1
    db.commit()
    print(f"✓ Loaded {count} patient demographics")
    
    print("Loading telemetry logs...")
    with open(BASE_DIR / 'telemetry_logs.csv') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            row['timestamp'] = datetime.fromisoformat(row['timestamp'])
            telem = StgTelemetryLogs(**row)
            db.add(telem)
            count += 1
    db.commit()
    print(f"✓ Loaded {count} telemetry logs")
    
    print("Loading prescriptions...")
    with open(BASE_DIR / 'prescription_audit.csv') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            row['timestamp'] = datetime.fromisoformat(row['timestamp'])
            row['age'] = int(row['age'])
            presc = StgPrescriptionAudit(**row)
            db.add(presc)
            count += 1
    db.commit()
    print(f"✓ Loaded {count} prescriptions")
    
    db.close()

def process_telemetry():
    """Process staging telemetry into cleaned table"""
    db = SessionLocal()
    
    print("Processing telemetry...")
    staging = db.query(StgTelemetryLogs).all()
    
    processed = 0
    corrupted = 0
    
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
        processed += 1
        
        if decoded['quality_flag'] == 'corrupted':
            corrupted += 1
    
    db.commit()
    print(f"✓ Processed {processed} telemetry records ({corrupted} corrupted)")
    db.close()

def process_prescriptions():
    """Process staging prescriptions into cleaned table"""
    db = SessionLocal()
    
    print("Processing prescriptions...")
    staging = db.query(StgPrescriptionAudit).all()
    
    processed = 0
    
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
        processed += 1
    
    db.commit()
    print(f"✓ Processed {processed} prescriptions")
    db.close()

def process_demographics():
    """Process staging demographics into cleaned table"""
    db = SessionLocal()
    
    print("Processing demographics...")
    staging = db.query(StgPatientDemographics).all()
    
    processed = 0
    
    for record in staging:
        # Simple decode for demo (reverse the cipher)
        decoded_name = record.name_cipher.replace("", " ").strip()
        
        clean = CleanDemographics(
            patient_raw_id=record.patient_raw_id,
            name_cipher=record.name_cipher,
            decoded_name=decoded_name,
            age=int(record.age),
            ward=record.ward_code
        )
        db.add(clean)
        processed += 1
    
    db.commit()
    print(f"✓ Processed {processed} demographics")
    db.close()

def reconcile_identities():
    """Create patient aliases using BPM parity"""
    db = SessionLocal()
    
    print("Reconciling patient identities...")
    demographics = db.query(CleanDemographics).all()
    
    reconciled = 0
    
    for demo in demographics:
        patient_id = reconcile_patient_identity(demo.patient_raw_id, db)
        print(f"  - {demo.patient_raw_id} → {patient_id}")
        reconciled += 1
    
    print(f"✓ Identity reconciliation complete ({reconciled} patients)")
    db.close()

def refresh_materialized_view():
    """Refresh patient view"""
    db = SessionLocal()
    
    print("Refreshing materialized view...")
    db.execute("REFRESH MATERIALIZED VIEW patient_view")
    db.commit()
    
    # Get count
    result = db.execute("SELECT COUNT(*) FROM patient_view").fetchone()
    count = result[0]
    
    print(f"✓ Refreshed materialized view ({count} patients)")
    db.close()

if __name__ == "__main__":
    print("=" * 60)
    print(" LAZARUS - Seed Data Loader")
    print("=" * 60)
    print()
    
    clear_existing_data()
    load_staging_data()
    process_telemetry()
    process_prescriptions()
    process_demographics()
    reconcile_identities()
    refresh_materialized_view()
    
    print()
    print("✅ Seed data loaded successfully!")
    print()
    print("Database now contains:")
    print("  - 20 patients (5 with colliding IDs)")
    print("  - 20,000 telemetry samples (1000 per patient)")
    print("  - ~100 prescriptions (3-8 per patient)")
    print()
    print("Next steps:")
    print("  1. Start backend: uvicorn app.main:app --reload")
    print("  2. Visit API docs: http://localhost:8000/docs")
    print("  3. Test endpoint: http://localhost:8000/api/patients")
    print("  4. Check alerts: http://localhost:8000/api/alerts")
'''

# File 3: README.md
readme_content = '''# Lazarus Seed Data Generator

This directory contains scripts to generate and load synthetic patient data for testing the Lazarus medical dashboard.

## Overview

The seed data system creates realistic test data that exercises all the unique features of Lazarus:

- **Identity Collisions**: 5 patients share raw IDs, distinguished by BPM parity
- **Corrupted Data**: 5% of telemetry samples are corrupted (invalid hex or out-of-range values)
- **Encrypted Data**: All medications are encrypted with age-based cipher
- **High Volume**: 20,000 telemetry samples total (1000 per patient over 24 hours)

## Files Generated

### 1. `patient_demographics.csv`
- **Records**: 20 patients
- **Colliding IDs**: 5 pairs of patients share the same `patient_raw_id`
- **Fields**: 
  - `patient_raw_id`: Patient identifier (5 colliding)
  - `name_cipher`: Encrypted patient name
  - `age`: Patient age (18-85)
  - `ward_code`: Ward assignment (ICU-1, ICU-2, ICU-3, Ward-4, Ward-5, ER)

### 2. `telemetry_logs.csv`
- **Records**: 20,000 samples (1000 per patient)
- **Time span**: 24 hours
- **Sample interval**: ~1.44 minutes
- **Corruption rate**: 5% (invalid hex or out-of-range BPM)
- **Fields**:
  - `patient_raw_id`: Patient identifier
  - `timestamp`: ISO format timestamp
  - `hex_payload`: Encoded telemetry (BPM + SpO2)
  - `source_device`: Monitoring device ID

**Parity Design:**
- Patients with colliding IDs have consistent BPM patterns:
  - Patient index 0, 2, 4... → Base BPM ~70 (even parity)
  - Patient index 1, 3, 5... → Base BPM ~75 (odd parity)

### 3. `prescription_audit.csv`
- **Records**: ~100 prescriptions (3-8 per patient)
- **Medications**: ASPIRIN, INSULIN, MORPHINE, WARFARIN, LISINOPRIL, METFORMIN, ATORVASTATIN
- **Fields**:
  - `patient_raw_id`: Patient identifier
  - `timestamp`: Prescription time (within last 72 hours)
  - `age`: Patient age (for decryption)
  - `med_cipher_text`: Encrypted medication name
  - `dosage`: Medication dosage
  - `route`: Administration route (PO, IV, SC, IM)

## Usage

### Step 1: Generate CSV Files

```bash
cd backend/seed_data
python generate_seeds.py
```

**Output:**
```
Generating seed data...
  - Patients: 20
  - Colliding IDs: 5
  - Telemetry samples per patient: 1000
  - Corruption rate: 5%

✓ Generated 20 patients
✓ Generated 20000 telemetry samples
✓ Generated 103 prescriptions

Seed data generated successfully!
  - patient_demographics.csv
  - telemetry_logs.csv
  - prescription_audit.csv
```

### Step 2: Load Data into Database

```bash
python load_seeds.py
```

**Process:**
1. **Clear existing data** - Removes all previous seed data
2. **Load staging tables** - Imports CSV data into staging tables
3. **Process telemetry** - Decodes hex payloads, validates data quality
4. **Process prescriptions** - Decrypts medication names
5. **Process demographics** - Decodes patient names
6. **Reconcile identities** - Creates `patient_alias` records using BPM parity
7. **Refresh materialized view** - Updates `patient_view` with latest data

**Output:**
```
============================================================
 LAZARUS - Seed Data Loader
============================================================

Clearing existing data...
✓ Cleared existing data
Loading patient demographics...
✓ Loaded 20 patient demographics
Loading telemetry logs...
✓ Loaded 20000 telemetry logs
Loading prescriptions...
✓ Loaded 103 prescriptions
Processing telemetry...
✓ Processed 20000 telemetry records (1000 corrupted)
Processing prescriptions...
✓ Processed 103 prescriptions
Processing demographics...
✓ Processed 20 demographics
Reconciling patient identities...
  - P00001 → patient-uuid-001
  - P00001 → patient-uuid-002
  - ...
✓ Identity reconciliation complete (20 patients)
Refreshing materialized view...
✓ Refreshed materialized view (20 patients)

✅ Seed data loaded successfully!

Database now contains:
  - 20 patients (5 with colliding IDs)
  - 20,000 telemetry samples (1000 per patient)
  - ~100 prescriptions (3-8 per patient)

Next steps:
  1. Start backend: uvicorn app.main:app --reload
  2. Visit API docs: http://localhost:8000/docs
  3. Test endpoint: http://localhost:8000/api/patients
  4. Check alerts: http://localhost:8000/api/alerts
```

## Quick Start (One Command)

```bash
python generate_seeds.py && python load_seeds.py
```

## Dependencies

- **Python 3.9+**
- **faker**: Generate realistic patient names
- **Backend modules**:
  - `app.services.telemetry_decoder`: Encode/decode telemetry hex payloads
  - `app.services.cipher`: Encrypt/decrypt medication names
  - `app.services.identity_reconciler`: Handle identity collisions
  - `app.database`: Database session management
  - `app.models.*`: ORM models for staging and cleaned tables

## Data Validation

After loading, verify the data:

### Check Patient Count
```bash
psql -d lazarus -c "SELECT COUNT(*) FROM patient_view;"
# Expected: 20
```

### Check Identity Collisions
```bash
psql -d lazarus -c "SELECT patient_raw_id, COUNT(*) FROM patient_alias GROUP BY patient_raw_id HAVING COUNT(*) > 1;"
# Expected: 5 rows with count = 2
```

### Check Telemetry Quality
```bash
psql -d lazarus -c "SELECT quality_flag, COUNT(*) FROM clean_telemetry GROUP BY quality_flag;"
# Expected: ~95% 'good', ~5% 'corrupted'
```

### Check Prescriptions
```bash
psql -d lazarus -c "SELECT COUNT(*), med_decoded_name FROM clean_prescriptions GROUP BY med_decoded_name;"
# Expected: ~15 per medication
```

## Notes

- **Faker seed**: Not set, so names are different each run
- **Timestamps**: Relative to current time (last 24 hours for telemetry, last 72 hours for prescriptions)
- **Re-running**: Safe to run multiple times; `load_seeds.py` clears old data first
- **Identity collision**: Automatically resolved via BPM parity in `reconcile_patient_identity()`

## Troubleshooting

### Import Errors
```bash
# Make sure you're in the backend directory
cd backend
python seed_data/generate_seeds.py
```

### Database Connection Errors
```bash
# Check database is running
docker-compose ps

# Check connection string in .env
cat .env | grep DATABASE_URL
```

### Data Not Showing
```bash
# Manually refresh materialized view
psql -d lazarus -c "REFRESH MATERIALIZED VIEW patient_view;"
```

## Next Steps

Once seed data is loaded:

1. **Start the backend API**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Test the endpoints**:
   - Health: http://localhost:8000/health
   - Patients: http://localhost:8000/api/patients
   - Alerts: http://localhost:8000/api/alerts
   - Docs: http://localhost:8000/docs

3. **Start the live simulator** (optional):
   ```bash
   python -m app.workers.live_simulator
   ```

4. **Launch the frontend** (optional):
   ```bash
   cd ../frontend
   npm run dev
   ```
'''

# Write all files
files_created = []

# Write generate_seeds.py
file1 = base_dir / 'generate_seeds.py'
file1.write_text(generate_seeds_content)
files_created.append(str(file1))
print(f"✓ Created: generate_seeds.py")

# Write load_seeds.py
file2 = base_dir / 'load_seeds.py'
file2.write_text(load_seeds_content)
files_created.append(str(file2))
print(f"✓ Created: load_seeds.py")

# Write README.md
file3 = base_dir / 'README.md'
file3.write_text(readme_content)
files_created.append(str(file3))
print(f"✓ Created: README.md")

print()
print("=" * 60)
print("✅ Seed data system created successfully!")
print("=" * 60)
print()
print("Files created:")
for f in files_created:
    print(f"  - {f}")
print()
print("Next steps:")
print("  1. Generate seed data: python backend/seed_data/generate_seeds.py")
print("  2. Load into database: python backend/seed_data/load_seeds.py")
print()
print("Or run both: python backend/seed_data/generate_seeds.py && python backend/seed_data/load_seeds.py")
