"""Prescription API response schemas"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PrescriptionResponse(BaseModel):
    id: int
    timestamp: datetime
    age: int
    med_cipher_text: str
    med_decoded_name: Optional[str] = None
    dosage: Optional[str] = None
    route: Optional[str] = None

    class Config:
        from_attributes = True
