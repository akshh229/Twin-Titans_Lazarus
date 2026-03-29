"""Development-only API helpers for demos and QA."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.alerts import PatientAlert
from app.models.cleaned import CleanTelemetry
from app.models.identity import PatientAlias
from app.models.staging import StgTelemetryLogs
from app.schemas.devtools import (
    TelemetrySimulationRequest,
    TelemetrySimulationResponse,
)
from app.services.alert_engine import process_vitals_for_alerts
from app.services.telemetry_decoder import encode_telemetry

router = APIRouter()


def _align_bpm_to_alias_parity(bpm: int, parity_flag: str) -> int:
    wants_even = parity_flag == "even"
    is_even = bpm % 2 == 0

    if wants_even == is_even:
        return bpm

    if bpm < settings.BPM_MAX:
        return bpm + 1

    return bpm - 1


@router.post(
    "/dev/simulate-telemetry",
    response_model=TelemetrySimulationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def simulate_telemetry(
    payload: TelemetrySimulationRequest,
    db: Session = Depends(get_db),
):
    """Insert one synthetic telemetry sample for a patient during local QA."""

    if settings.ENVIRONMENT.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Telemetry simulation is disabled in production.",
        )

    alias = (
        db.query(PatientAlias)
        .filter(PatientAlias.patient_id == payload.patient_id)
        .first()
    )
    if alias is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient alias not found.",
        )

    applied_bpm = _align_bpm_to_alias_parity(payload.bpm, alias.parity_flag)
    timestamp = datetime.utcnow()
    hex_payload = encode_telemetry(applied_bpm, payload.oxygen)

    db.add(
        StgTelemetryLogs(
            patient_raw_id=alias.patient_raw_id,
            timestamp=timestamp,
            hex_payload=hex_payload,
            source_device=payload.source_device,
        )
    )
    db.add(
        CleanTelemetry(
            patient_raw_id=alias.patient_raw_id,
            timestamp=timestamp,
            hex_payload=hex_payload,
            bpm=applied_bpm,
            oxygen=payload.oxygen,
            parity_flag=alias.parity_flag,
            quality_flag="good",
        )
    )
    db.flush()

    process_vitals_for_alerts(payload.patient_id, applied_bpm, payload.oxygen, db)

    latest_alert = (
        db.query(PatientAlert)
        .filter(PatientAlert.patient_id == payload.patient_id)
        .order_by(PatientAlert.opened_at.desc())
        .first()
    )

    return TelemetrySimulationResponse(
        patient_id=payload.patient_id,
        patient_raw_id=alias.patient_raw_id,
        requested_bpm=payload.bpm,
        applied_bpm=applied_bpm,
        oxygen=payload.oxygen,
        parity_flag=alias.parity_flag,
        adjusted_for_identity=applied_bpm != payload.bpm,
        timestamp=timestamp,
        alert_status=latest_alert.status if latest_alert else None,
    )
