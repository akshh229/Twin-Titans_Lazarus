"""Alert API response schemas"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AlertResponse(BaseModel):
    id: int
    patient_id: UUID
    alert_type: str
    opened_at: datetime
    last_bpm: Optional[int] = None
    last_oxygen: Optional[int] = None
    status: str
    consecutive_abnormal_count: int
    patient_name: Optional[str] = None
    age: Optional[int] = None
    ward: Optional[str] = None

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    last_bpm: int
    last_oxygen: int
    status: str

    class Config:
        from_attributes = True
