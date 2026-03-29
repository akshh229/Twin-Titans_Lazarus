"""
Live Simulator - Generates fake telemetry every 5 seconds for demo purposes
Run this alongside the backend to make the dashboard feel alive.
"""

import time
import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.staging import StgTelemetryLogs
from app.models.cleaned import CleanTelemetry
from app.services.telemetry_decoder import decode_telemetry, encode_telemetry
from app.services.identity_reconciler import reconcile_patient_identity
from app.services.alert_engine import process_vitals_for_alerts


def get_active_patients(db: Session):
    """Get list of patient raw IDs from the database."""
    from app.models.cleaned import CleanDemographics

    patients = db.query(CleanDemographics.patient_raw_id).distinct().all()
    return [p[0] for p in patients]


def simulate_vitals_batch(db: Session, patients: list[str]):
    """Generate one batch of new vitals for all patients."""
    for raw_id in patients:
        # Random BPM with occasional abnormal values
        if random.random() < 0.1:  # 10% chance of abnormal
            bpm = random.choice(
                [
                    random.randint(40, 58),  # Bradycardia
                    random.randint(102, 145),  # Tachycardia
                ]
            )
        else:
            bpm = random.randint(60, 100)

        spo2 = random.randint(94, 100)
        hex_payload = encode_telemetry(bpm, spo2)
        now = datetime.utcnow()

        # Write to staging
        staging = StgTelemetryLogs(
            patient_raw_id=raw_id,
            timestamp=now,
            hex_payload=hex_payload,
            source_device="SIMULATOR",
        )
        db.add(staging)
        db.flush()

        # Decode and write to cleaned
        decoded = decode_telemetry(hex_payload)
        clean = CleanTelemetry(
            staging_log_id=staging.id,
            patient_raw_id=raw_id,
            timestamp=now,
            hex_payload=hex_payload,
            bpm=decoded["bpm"],
            oxygen=decoded["oxygen"],
            parity_flag=decoded["parity_flag"],
            quality_flag=decoded["quality_flag"],
        )
        db.add(clean)

        # Process alerts
        if decoded["quality_flag"] == "good":
            try:
                patient_id = reconcile_patient_identity(raw_id, clean.id, db)
                process_vitals_for_alerts(
                    patient_id, decoded["bpm"], decoded["oxygen"], db
                )
            except Exception:
                pass

    db.commit()


def run_simulator(interval: float = 5.0):
    """Main simulator loop."""
    print("=" * 60)
    print(" LAZARUS Live Simulator")
    print(f" Generating telemetry every {interval} seconds")
    print(" Press Ctrl+C to stop")
    print("=" * 60)
    print()

    db = SessionLocal()
    patients = get_active_patients(db)

    if not patients:
        print("No patients found in database.")
        print("Run seed data loader first: python seed_data/load_seeds.py")
        return

    print(f"Simulating vitals for {len(patients)} patients...")
    print()

    batch = 0
    try:
        while True:
            batch += 1
            simulate_vitals_batch(db, patients)
            print(
                f"  Batch {batch}: Generated vitals for {len(patients)} patients at {datetime.utcnow().strftime('%H:%M:%S')}"
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
    finally:
        db.close()


if __name__ == "__main__":
    run_simulator()
