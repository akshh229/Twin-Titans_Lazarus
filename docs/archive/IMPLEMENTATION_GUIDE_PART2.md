# LAZARUS - IMPLEMENTATION GUIDE PART 2
## API Endpoints & Schemas

---

## SECTION 3: API ENDPOINTS

### File: `backend/app/api/patients.py`

```python
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


@app.get("/patients", response_model=List[PatientListResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all patients with last vitals and alert status.
    Uses materialized view for optimized performance.
    """
    # Query from materialized view (create this in migrations)
    query = text("""
        SELECT 
            patient_id,
            patient_raw_id,
            parity_flag,
            decoded_name as name,
            age,
            ward,
            last_bpm,
            last_oxygen,
            last_vitals_timestamp,
            quality_flag,
            prescription_count,
            has_active_alert
        FROM patient_view
        ORDER BY has_active_alert DESC, decoded_name ASC
        LIMIT :limit OFFSET :skip
    """)
    
    result = db.execute(query, {"limit": limit, "skip": skip})
    patients = [dict(row._mapping) for row in result]
    
    return patients


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_detail(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed patient information including identity confidence.
    """
    # Get patient alias info
    from app.models.identity import PatientAlias
    
    alias = db.query(PatientAlias)\
        .filter(PatientAlias.patient_id == patient_id)\
        .first()
    
    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get from materialized view
    query = text("""
        SELECT * FROM patient_view WHERE patient_id = :patient_id
    """)
    
    result = db.execute(query, {"patient_id": str(patient_id)}).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Patient not found in view")
    
    patient_data = dict(result._mapping)
    patient_data['identity_confidence'] = float(alias.confidence_score)
    patient_data['identity_sample_count'] = alias.sample_count
    
    return patient_data
```

### File: `backend/app/api/vitals.py`

```python
"""
Vitals API Endpoints
Provides time-series vitals data for charts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.database import get_db
from app.models.cleaned import CleanTelemetry
from app.models.identity import PatientAlias
from app.schemas.telemetry import VitalsTimeSeriesResponse, VitalsDataPoint

router = APIRouter()


@router.get("/patients/{patient_id}/vitals", response_model=VitalsTimeSeriesResponse)
async def get_patient_vitals(
    patient_id: UUID,
    hours: int = Query(default=24, ge=1, le=168),  # Max 1 week
    db: Session = Depends(get_db)
):
    """
    Get time-series vitals data for patient.
    
    Args:
        patient_id: Unique patient identifier
        hours: Number of hours of history (default 24)
    
    Returns:
        Time-series array of BPM and SpO2 readings
    """
    # Get patient alias to find raw_id and parity
    alias = db.query(PatientAlias)\
        .filter(PatientAlias.patient_id == patient_id)\
        .first()
    
    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Calculate time window
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Query telemetry
    vitals = db.query(CleanTelemetry)\
        .filter(and_(
            CleanTelemetry.patient_raw_id == alias.patient_raw_id,
            CleanTelemetry.parity_flag == alias.parity_flag,
            CleanTelemetry.timestamp >= start_time,
            CleanTelemetry.timestamp <= end_time,
            CleanTelemetry.quality_flag == 'good'
        ))\
        .order_by(CleanTelemetry.timestamp.asc())\
        .all()
    
    data_points = [
        {
            "timestamp": v.timestamp,
            "bpm": v.bpm,
            "oxygen": v.oxygen,
            "quality_flag": v.quality_flag
        }
        for v in vitals
    ]
    
    return {
        "patient_id": patient_id,
        "start_time": start_time,
        "end_time": end_time,
        "data": data_points
    }
```

### File: `backend/app/api/prescriptions.py`

```python
"""
Prescriptions API Endpoints
Shows encrypted vs decrypted medication names
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.cleaned import CleanPrescriptions
from app.models.identity import PatientAlias
from app.schemas.prescription import PrescriptionResponse

router = APIRouter()


@router.get("/patients/{patient_id}/prescriptions", response_model=List[PrescriptionResponse])
async def get_patient_prescriptions(
    patient_id: UUID,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get medications for patient with both encrypted and decrypted names.
    Demonstrates age-cipher decryption.
    """
    # Get patient alias
    alias = db.query(PatientAlias)\
        .filter(PatientAlias.patient_id == patient_id)\
        .first()
    
    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Query prescriptions
    prescriptions = db.query(CleanPrescriptions)\
        .filter(CleanPrescriptions.patient_raw_id == alias.patient_raw_id)\
        .order_by(CleanPrescriptions.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return [
        {
            "id": p.id,
            "timestamp": p.timestamp,
            "age": p.age,
            "med_cipher_text": p.med_cipher_text,
            "med_decoded_name": p.med_decoded_name,
            "dosage": p.dosage,
            "route": p.route
        }
        for p in prescriptions
    ]
```

### File: `backend/app/api/alerts.py`

```python
"""
Alerts API Endpoints
Critical vitals alerts management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.alerts import PatientAlert
from app.schemas.alert import AlertResponse, AlertHistoryResponse
from app.services.alert_engine import get_open_alerts, get_patient_alert_history

router = APIRouter()


@router.get("/alerts", response_model=List[AlertResponse])
async def list_active_alerts(db: Session = Depends(get_db)):
    """
    Get all currently open critical alerts.
    Returns alerts with patient information for dashboard.
    """
    query = text("""
        SELECT 
            pa.id,
            pa.patient_id,
            pa.alert_type,
            pa.opened_at,
            pa.last_bpm,
            pa.last_oxygen,
            pa.status,
            pa.consecutive_abnormal_count,
            pv.decoded_name as patient_name,
            pv.age,
            pv.ward
        FROM patient_alerts pa
        JOIN patient_view pv ON pa.patient_id = pv.patient_id
        WHERE pa.status = 'open'
        ORDER BY pa.opened_at DESC
    """)
    
    result = db.execute(query)
    alerts = [dict(row._mapping) for row in result]
    
    return alerts


@router.get("/alerts/history/{patient_id}", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get alert history for a specific patient.
    Shows closed alerts with duration information.
    """
    alerts = get_patient_alert_history(patient_id, db)
    
    return [
        {
            "id": a.id,
            "opened_at": a.opened_at,
            "closed_at": a.closed_at,
            "duration_minutes": int((a.closed_at - a.opened_at).total_seconds() / 60) if a.closed_at else None,
            "last_bpm": a.last_bpm,
            "last_oxygen": a.last_oxygen,
            "status": a.status
        }
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark alert as acknowledged by clinician.
    """
    alert = db.query(PatientAlert).filter(PatientAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = 'acknowledged'
    db.commit()
    
    return {"status": "acknowledged", "alert_id": alert_id}
```

---

## SECTION 4: PYDANTIC SCHEMAS

### File: `backend/app/schemas/patient.py`

```python
"""Patient API response schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class PatientListResponse(BaseModel):
    """Schema for patient list endpoint"""
    patient_id: UUID
    patient_raw_id: str
    parity_flag: str
    name: Optional[str]
    age: Optional[int]
    ward: Optional[str]
    last_bpm: Optional[int]
    last_oxygen: Optional[int]
    last_vitals_timestamp: Optional[datetime]
    quality_flag: Optional[str]
    prescription_count: int
    has_active_alert: bool
    
    class Config:
        from_attributes = True


class PatientDetailResponse(PatientListResponse):
    """Extended schema with identity reconciliation info"""
    identity_confidence: float
    identity_sample_count: int
```

### File: `backend/app/schemas/telemetry.py`

```python
"""Telemetry API response schemas"""
from pydantic import BaseModel
from typing import List
from datetime import datetime
from uuid import UUID


class VitalsDataPoint(BaseModel):
    """Single vitals measurement"""
    timestamp: datetime
    bpm: int
    oxygen: int
    quality_flag: str
    
    class Config:
        from_attributes = True


class VitalsTimeSeriesResponse(BaseModel):
    """Time-series vitals data for charts"""
    patient_id: UUID
    start_time: datetime
    end_time: datetime
    data: List[VitalsDataPoint]
```

### File: `backend/app/schemas/prescription.py`

```python
"""Prescription API response schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PrescriptionResponse(BaseModel):
    """Prescription with both encrypted and decrypted medication names"""
    id: int
    timestamp: datetime
    age: int
    med_cipher_text: str
    med_decoded_name: Optional[str]
    dosage: Optional[str]
    route: Optional[str]
    
    class Config:
        from_attributes = True
```

### File: `backend/app/schemas/alert.py`

```python
"""Alert API response schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AlertResponse(BaseModel):
    """Active alert with patient information"""
    id: int
    patient_id: UUID
    alert_type: str
    opened_at: datetime
    last_bpm: int
    last_oxygen: int
    status: str
    consecutive_abnormal_count: int
    patient_name: Optional[str]
    age: Optional[int]
    ward: Optional[str]
    
    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    """Historical alert record"""
    id: int
    opened_at: datetime
    closed_at: Optional[datetime]
    duration_minutes: Optional[int]
    last_bpm: int
    last_oxygen: int
    status: str
    
    class Config:
        from_attributes = True
```

---

## SECTION 5: WEBSOCKET IMPLEMENTATION

### File: `backend/app/websocket/vitals_stream.py`

```python
"""
WebSocket Server for Real-Time Vitals Streaming
Broadcasts vitals updates and alerts to connected clients
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
from uuid import UUID
import json
import asyncio

from app.database import get_db
from app.config import settings

router = APIRouter()

# Active WebSocket connections
# Format: {patient_id: set of WebSocket connections}
active_connections: Dict[UUID, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, patient_id: UUID):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = set()
        
        self.active_connections[patient_id].add(websocket)
        print(f"✓ Client connected to patient {patient_id}")
    
    def disconnect(self, websocket: WebSocket, patient_id: UUID):
        """Remove WebSocket connection"""
        if patient_id in self.active_connections:
            self.active_connections[patient_id].discard(websocket)
            
            if not self.active_connections[patient_id]:
                del self.active_connections[patient_id]
        
        print(f"✗ Client disconnected from patient {patient_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_json(message)
    
    async def broadcast_to_patient(self, message: dict, patient_id: UUID):
        """Broadcast message to all clients watching this patient"""
        if patient_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[patient_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up dead connections
            for conn in disconnected:
                self.active_connections[patient_id].discard(conn)


manager = ConnectionManager()


@router.websocket("/vitals/{patient_id}")
async def vitals_websocket_endpoint(
    websocket: WebSocket,
    patient_id: UUID
):
    """
    WebSocket endpoint for real-time vitals streaming.
    
    Client sends: {"type": "subscribe", "patient_id": "uuid"}
    Server sends: {
        "type": "vitals_update",
        "patient_id": "uuid",
        "timestamp": "...",
        "bpm": 76,
        "oxygen": 97
    }
    """
    await manager.connect(websocket, patient_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": str(datetime.utcnow())},
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, patient_id)


async def broadcast_vitals_update(patient_id: UUID, bpm: int, oxygen: int, timestamp: datetime):
    """
    Called by telemetry processor to broadcast new vitals.
    This is the function that external code calls to push updates.
    """
    message = {
        "type": "vitals_update",
        "patient_id": str(patient_id),
        "timestamp": timestamp.isoformat(),
        "bpm": bpm,
        "oxygen": oxygen
    }
    
    await manager.broadcast_to_patient(message, patient_id)


async def broadcast_alert_opened(patient_id: UUID, patient_name: str, bpm: int):
    """Broadcast alert opened event"""
    message = {
        "type": "alert_opened",
        "patient_id": str(patient_id),
        "patient_name": patient_name,
        "last_bpm": bpm
    }
    
    await manager.broadcast_to_patient(message, patient_id)


async def broadcast_alert_closed(patient_id: UUID):
    """Broadcast alert closed event"""
    message = {
        "type": "alert_closed",
        "patient_id": str(patient_id)
    }
    
    await manager.broadcast_to_patient(message, patient_id)
```

---

## FILE PROGRESS

**Completed:**
- ✅ Core Services (4 files)
- ✅ API Endpoints (4 files)
- ✅ Pydantic Schemas (4 files)
- ✅ WebSocket Handler (1 file)

**Remaining:**
- ⏳ Data Ingestion Service
- ⏳ Background Workers
- ⏳ Database Migrations
- ⏳ Tests
- ⏳ Seed Data Generator
- ⏳ Frontend (React)

**Next:** Part 3 - Workers, Migrations & Seed Data

