"""Telemetry API response schemas"""

from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime
from uuid import UUID


class VitalsDataPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    bpm: int
    oxygen: int
    quality_flag: str


class VitalsTimeSeriesResponse(BaseModel):
    patient_id: UUID
    start_time: datetime
    end_time: datetime
    data: List[VitalsDataPoint]
