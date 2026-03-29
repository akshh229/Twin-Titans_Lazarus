"""Telemetry API response schemas"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class VitalsDataPoint(BaseModel):
    timestamp: datetime
    bpm: int
    oxygen: int
    quality_flag: str

    class Config:
        from_attributes = True


class VitalsTimeSeriesResponse(BaseModel):
    patient_id: UUID
    start_time: datetime
    end_time: datetime
    data: List[VitalsDataPoint]
