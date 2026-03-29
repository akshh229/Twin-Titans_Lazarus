"""Load seed data into database"""

import csv
from pathlib import Path
from datetime import datetime

from sqlalchemy import text

from app.database import SessionLocal
from app.models.staging import (
    StgPatientDemographics,
    StgTelemetryLogs,
    StgPrescriptionAudit,
)
from app.models.cleaned import CleanTelemetry, CleanPrescriptions, CleanDemographics
from app.services.telemetry_decoder import decode_telemetry
from app.services.cipher import decrypt_medication
from app.services.identity_reconciler import reconcile_patient_identity

BASE_DIR = Path(__file__).parent


def load_staging_data():
    """Load CSV files into staging tables"""
    db = SessionLocal()

    print("Loading patient demographics...")
    with open(BASE_DIR / "patient_demographics.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            demo = StgPatientDemographics(**row)
            db.add(demo)
    db.commit()
    print("  Done")

    print("Loading telemetry logs...")
    with open(BASE_DIR / "telemetry_logs.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            telem = StgTelemetryLogs(**row)
            db.add(telem)
    db.commit()
    print("  Done")

    print("Loading prescriptions...")
    with open(BASE_DIR / "prescription_audit.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["timestamp"] = datetime.fromisoformat(row["timestamp"])
            row["age"] = int(row["age"])
            presc = StgPrescriptionAudit(**row)
            db.add(presc)
    db.commit()
    print("  Done")

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
            bpm=decoded["bpm"],
            oxygen=decoded["oxygen"],
            parity_flag=decoded["parity_flag"],
            quality_flag=decoded["quality_flag"],
        )
        db.add(clean)

    db.commit()
    print(f"  Processed {len(staging)} records")
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
            route=record.route,
        )
        db.add(clean)

    db.commit()
    print(f"  Processed {len(staging)} records")
    db.close()


def _decode_patient_name(name_cipher: str) -> str:
    """Decode name cipher (uppercase, no spaces) back to readable name.

    Name cipher format: "JOHNSMITH" -> we split heuristically.
    Since the original format is "FIRST LAST", we try common split points.
    """
    if not name_cipher:
        return "Unknown"

    # Try splitting at each position and pick the one where both parts
    # look like reasonable names (2+ chars each, all alpha)
    name = name_cipher.upper()
    best_split = None

    for i in range(2, len(name) - 1):
        first = name[:i]
        last = name[i:]
        if first.isalpha() and last.isalpha() and len(first) >= 2 and len(last) >= 2:
            best_split = (first, last)
            # Prefer split points that match common name boundaries
            if last[0] not in "AEIOU":
                break

    if best_split:
        return f"{best_split[0].title()} {best_split[1].title()}"
    return name_cipher.title()


def process_demographics():
    """Process staging demographics into cleaned table"""
    db = SessionLocal()

    print("Processing demographics...")
    staging = db.query(StgPatientDemographics).all()

    for record in staging:
        clean = CleanDemographics(
            patient_raw_id=record.patient_raw_id,
            name_cipher=record.name_cipher,
            decoded_name=_decode_patient_name(record.name_cipher),
            age=record.age,
            ward=record.ward_code,
        )
        db.add(clean)

    db.commit()
    print(f"  Processed {len(staging)} records")
    db.close()


def reconcile_identities():
    """Create patient aliases using BPM parity"""
    db = SessionLocal()

    print("Reconciling patient identities...")
    demographics = db.query(CleanDemographics).all()

    for demo in demographics:
        patient_id = reconcile_patient_identity(demo.patient_raw_id, db)
        print(f"  {demo.patient_raw_id} -> {patient_id}")

    print("  Done")
    db.close()


def refresh_materialized_view():
    """Refresh patient view"""
    db = SessionLocal()
    db.execute(text("REFRESH MATERIALIZED VIEW patient_view"))
    db.commit()
    print("Refreshed materialized view")
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
    print("Seed data loaded successfully!")
    print("  1. Start backend: uvicorn app.main:app --reload")
    print("  2. API docs: http://localhost:8000/docs")
    print("  3. Test: http://localhost:8000/api/patients")
