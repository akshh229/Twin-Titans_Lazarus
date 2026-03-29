"""Patient API response schemas"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class PatientListResponse(BaseModel):
    patient_id: UUID
    patient_raw_id: str
    parity_flag: str
    name: Optional[str] = None
    age: Optional[int] = None
    ward: Optional[str] = None
    last_bpm: Optional[int] = None
    last_oxygen: Optional[int] = None
    last_vitals_timestamp: Optional[datetime] = None
    quality_flag: Optional[str] = None
    prescription_count: int = 0
    has_active_alert: bool = False

    class Config:
        from_attributes = True


class PatientDetailResponse(PatientListResponse):
    identity_confidence: float = 0.0
    identity_sample_count: int = 0
