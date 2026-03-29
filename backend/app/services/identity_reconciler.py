"""
Identity Reconciliation - Uses BPM parity to disambiguate patients
"""

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.cleaned import CleanTelemetry
from app.models.identity import PatientAlias, IdentityAuditLog
from app.config import settings


def reconcile_patient_identity(patient_raw_id: str, db: Session) -> UUID:
    """
    Determine unique patient_id from raw_id using BPM parity.

    Algorithm:
    1. Fetch recent good-quality BPM samples
    2. Count even vs odd BPM readings
    3. Dominant parity determines patient identity
    4. Create/lookup (raw_id, parity) -> patient_id mapping

    Returns:
        UUID: Unique patient identifier
    """
    recent_samples = (
        db.query(CleanTelemetry)
        .filter(CleanTelemetry.patient_raw_id == patient_raw_id)
        .filter(CleanTelemetry.quality_flag == "good")
        .order_by(CleanTelemetry.timestamp.desc())
        .limit(settings.PARITY_SAMPLE_COUNT)
        .all()
    )

    if not recent_samples:
        parity = "even"
        confidence = 0.3
        sample_count = 0
    else:
        even_count = sum(1 for s in recent_samples if s.parity_flag == "even")
        odd_count = len(recent_samples) - even_count

        parity = "even" if even_count >= odd_count else "odd"
        confidence = round(max(even_count, odd_count) / len(recent_samples), 2)
        sample_count = len(recent_samples)

    alias = (
        db.query(PatientAlias)
        .filter_by(patient_raw_id=patient_raw_id, parity_flag=parity)
        .first()
    )

    if not alias:
        alias = PatientAlias(
            patient_raw_id=patient_raw_id,
            parity_flag=parity,
            sample_count=sample_count,
            confidence_score=confidence,
        )
        db.add(alias)
        try:
            db.commit()
            db.refresh(alias)
        except IntegrityError:
            db.rollback()
            alias = (
                db.query(PatientAlias)
                .filter_by(patient_raw_id=patient_raw_id, parity_flag=parity)
                .first()
            )
            if alias:
                alias.sample_count = sample_count
                alias.confidence_score = confidence
                db.commit()
                return alias.patient_id
            raise

        audit = IdentityAuditLog(
            patient_id=alias.patient_id,
            patient_raw_id=patient_raw_id,
            parity_flag=parity,
            action="created",
            bpm_samples_used=sample_count,
            decision_reason=f"Dominant parity: {parity} ({confidence:.0%} confidence from {sample_count} samples)",
        )
        db.add(audit)
        db.commit()
    else:
        alias.sample_count = sample_count
        alias.confidence_score = confidence
        db.commit()

    return alias.patient_id
