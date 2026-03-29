"""
Vitals API Endpoints
Provides time-series vitals data for charts
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.cleaned import CleanTelemetry
from app.models.identity import PatientAlias
from app.schemas.telemetry import VitalsTimeSeriesResponse

router = APIRouter()


@router.get("/patients/{patient_id}/vitals", response_model=VitalsTimeSeriesResponse)
async def get_patient_vitals(
    patient_id: UUID,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get time-series vitals data for patient charts."""
    alias = db.query(PatientAlias).filter(PatientAlias.patient_id == patient_id).first()

    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)

    vitals = (
        db.query(CleanTelemetry)
        .filter(
            and_(
                CleanTelemetry.patient_raw_id == alias.patient_raw_id,
                CleanTelemetry.parity_flag == alias.parity_flag,
                CleanTelemetry.timestamp >= start_time,
                CleanTelemetry.timestamp <= end_time,
                CleanTelemetry.quality_flag == "good",
            )
        )
        .order_by(CleanTelemetry.timestamp.asc())
        .all()
    )

    data_points = [
        {
            "timestamp": v.timestamp,
            "bpm": v.bpm,
            "oxygen": v.oxygen,
            "quality_flag": v.quality_flag,
        }
        for v in vitals
    ]

    return {
        "patient_id": patient_id,
        "start_time": start_time,
        "end_time": end_time,
        "data": data_points,
    }
