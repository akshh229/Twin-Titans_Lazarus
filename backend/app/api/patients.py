"""
Patient API Endpoints
Provides patient list, detail, and search functionality
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.patient import PatientListResponse, PatientDetailResponse

router = APIRouter()


@router.get("/patients", response_model=List[PatientListResponse])
async def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all patients with last vitals and alert status."""
    query = text("""
        SELECT
            pa.patient_id,
            pa.patient_raw_id,
            pa.parity_flag,
            cd.decoded_name as name,
            cd.age,
            cd.ward,
            latest_vitals.bpm AS last_bpm,
            latest_vitals.oxygen AS last_oxygen,
            latest_vitals.timestamp AS last_vitals_timestamp,
            latest_vitals.quality_flag,
            COALESCE(presc_count.cnt, 0) AS prescription_count,
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
        LEFT JOIN (
            SELECT patient_raw_id, COUNT(*) AS cnt
            FROM clean_prescriptions
            GROUP BY patient_raw_id
        ) presc_count ON presc_count.patient_raw_id = pa.patient_raw_id
        ORDER BY has_active_alert DESC, cd.decoded_name ASC
        LIMIT :limit OFFSET :skip
    """)

    result = db.execute(query, {"limit": limit, "skip": skip})
    patients = [dict(row._mapping) for row in result]
    return patients


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_detail(patient_id: UUID, db: Session = Depends(get_db)):
    """Get detailed patient information including identity confidence."""
    from app.models.identity import PatientAlias

    alias = db.query(PatientAlias).filter(PatientAlias.patient_id == patient_id).first()

    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")

    query = text("""
        SELECT
            pa.patient_id,
            pa.patient_raw_id,
            pa.parity_flag,
            cd.decoded_name as name,
            cd.age,
            cd.ward,
            latest_vitals.bpm AS last_bpm,
            latest_vitals.oxygen AS last_oxygen,
            latest_vitals.timestamp AS last_vitals_timestamp,
            latest_vitals.quality_flag,
            COALESCE(presc_count.cnt, 0) AS prescription_count,
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
        LEFT JOIN (
            SELECT patient_raw_id, COUNT(*) AS cnt
            FROM clean_prescriptions
            GROUP BY patient_raw_id
        ) presc_count ON presc_count.patient_raw_id = pa.patient_raw_id
        WHERE pa.patient_id = :patient_id
    """)

    result = db.execute(query, {"patient_id": str(patient_id)}).first()

    if not result:
        raise HTTPException(status_code=404, detail="Patient not found in view")

    patient_data = dict(result._mapping)
    patient_data["identity_confidence"] = float(alias.confidence_score)
    patient_data["identity_sample_count"] = alias.sample_count

    return patient_data
