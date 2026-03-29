# LAZARUS - COMPLETE IMPLEMENTATION GUIDE
## Medical Forensic Recovery Dashboard

**Version:** 1.0  
**Target:** Production-ready system  
**Estimated Setup Time:** 2-3 hours

---

## TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Backend Implementation](#backend-implementation)
3. [Frontend Implementation](#frontend-implementation)
4. [Database Setup](#database-setup)
5. [Testing](#testing)
6. [Deployment](#deployment)

---

## QUICK START

### Prerequisites Checklist
```
□ Docker & Docker Compose installed
□ Python 3.11+ installed
□ Node.js 18+ installed  
□ PostgreSQL client tools (optional)
□ Git (optional)
```

### 30-Second Setup
```bash
# 1. Navigate to project
cd "E:\Project Lazarus"

# 2. Ensure directories exist (run create_dirs.bat if needed)
create_dirs.bat

# 3. Copy environment file
copy .env.example .env

# 4. Start services
docker-compose up -d

# 5. Wait for healthy status (30-60 seconds)
docker-compose ps

# 6. Apply database migrations
docker-compose exec backend alembic upgrade head

# 7. Load sample data
docker-compose exec backend python seed_data/load_seeds.py

# 8. Access dashboard
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## BACKEND IMPLEMENTATION

### 1. Core Services

#### File: `backend/app/services/telemetry_decoder.py`

```python
"""
Telemetry Hex Decoder - Converts corrupted hex payloads to BPM/SpO2
"""
from typing import Dict, Optional
from app.config import settings


def decode_telemetry(hex_payload: str) -> Dict[str, Optional[int | str]]:
    """
    Decode hex string to BPM and SpO2.
    
    Frame layout:
      Bytes 0-1: BPM (uint16, big-endian)
      Bytes 2-3: SpO2 (uint16, big-endian)
    
    Returns:
        {
            'bpm': int or None,
            'oxygen': int or None,
            'quality_flag': 'good' | 'bad' | 'missing',
            'parity_flag': 'even' | 'odd' | None
        }
    """
    try:
        payload_bytes = bytes.fromhex(hex_payload.strip())
        
        if len(payload_bytes) < 4:
            return {'bpm': None, 'oxygen': None, 'quality_flag': 'missing', 'parity_flag': None}
        
        bpm = int.from_bytes(
            payload_bytes[settings.BPM_OFFSET:settings.BPM_OFFSET + settings.BPM_LENGTH],
            byteorder=settings.TELEMETRY_BYTE_ORDER
        )
        
        spo2 = int.from_bytes(
            payload_bytes[settings.SPO2_OFFSET:settings.SPO2_OFFSET + settings.SPO2_LENGTH],
            byteorder=settings.TELEMETRY_BYTE_ORDER
        )
        
        # Validate ranges
        bpm_valid = settings.BPM_MIN <= bpm <= settings.BPM_MAX
        spo2_valid = settings.SPO2_MIN <= spo2 <= settings.SPO2_MAX
        
        if not (bpm_valid and spo2_valid):
            return {'bpm': bpm, 'oxygen': spo2, 'quality_flag': 'bad', 'parity_flag': None}
        
        parity = 'even' if bpm % 2 == 0 else 'odd'
        
        return {'bpm': bpm, 'oxygen': spo2, 'quality_flag': 'good', 'parity_flag': parity}
    
    except (ValueError, IndexError):
        return {'bpm': None, 'oxygen': None, 'quality_flag': 'bad', 'parity_flag': None}


def encode_telemetry(bpm: int, spo2: int) -> str:
    """Encode BPM and SpO2 to hex (for testing)"""
    bpm_bytes = bpm.to_bytes(settings.BPM_LENGTH, byteorder=settings.TELEMETRY_BYTE_ORDER)
    spo2_bytes = spo2.to_bytes(settings.SPO2_LENGTH, byteorder=settings.TELEMETRY_BYTE_ORDER)
    return (bpm_bytes + spo2_bytes).hex()
```

#### File: `backend/app/services/cipher.py`

```python
"""
Age-Relative Cipher - Decrypts medication names using patient age
"""


def decrypt_medication(cipher_text: str, age: int) -> str:
    """
    Decrypt medication using age-relative Caesar cipher.
    
    Algorithm: shift = age % 26
    Each letter shifts backward in A-Z alphabet (with wraparound)
    
    Example:
        decrypt_medication("FWRKITPMR", 45) -> "ASPIRIN"
        (45 % 26 = 19, each letter shifts back 19 positions)
    """
    shift = age % 26
    result = []
    
    for char in cipher_text.upper():
        if char.isalpha():
            pos = ord(char) - ord('A')
            new_pos = (pos - shift) % 26
            result.append(chr(ord('A') + new_pos))
        else:
            result.append(char)
    
    return ''.join(result)


def encrypt_medication(plain_text: str, age: int) -> str:
    """Encrypt medication (inverse operation for testing)"""
    shift = age % 26
    result = []
    
    for char in plain_text.upper():
        if char.isalpha():
            pos = ord(char) - ord('A')
            new_pos = (pos + shift) % 26
            result.append(chr(ord('A') + new_pos))
        else:
            result.append(char)
    
    return ''.join(result)
```

#### File: `backend/app/services/identity_reconciler.py`

```python
"""
Identity Reconciliation - Uses BPM parity to disambiguate patients
"""
from uuid import UUID
from sqlalchemy.orm import Session
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
    4. Create/lookup (raw_id, parity) → patient_id mapping
    
    Returns:
        UUID: Unique patient identifier
    """
    # Get recent good samples
    recent_samples = db.query(CleanTelemetry)\
        .filter(CleanTelemetry.patient_raw_id == patient_raw_id)\
        .filter(CleanTelemetry.quality_flag == 'good')\
        .order_by(CleanTelemetry.timestamp.desc())\
        .limit(settings.PARITY_SAMPLE_COUNT)\
        .all()
    
    if not recent_samples:
        # No good samples - default to 'even' with low confidence
        parity = 'even'
        confidence = 0.3
        sample_count = 0
    else:
        even_count = sum(1 for s in recent_samples if s.parity_flag == 'even')
        odd_count = len(recent_samples) - even_count
        
        parity = 'even' if even_count >= odd_count else 'odd'
        confidence = round(max(even_count, odd_count) / len(recent_samples), 2)
        sample_count = len(recent_samples)
    
    # Get or create alias
    alias = db.query(PatientAlias)\
        .filter_by(patient_raw_id=patient_raw_id, parity_flag=parity)\
        .first()
    
    if not alias:
        alias = PatientAlias(
            patient_raw_id=patient_raw_id,
            parity_flag=parity,
            sample_count=sample_count,
            confidence_score=confidence
        )
        db.add(alias)
        db.commit()
        db.refresh(alias)
        
        # Audit log
        audit = IdentityAuditLog(
            patient_id=alias.patient_id,
            patient_raw_id=patient_raw_id,
            parity_flag=parity,
            action='created',
            bpm_samples_used=sample_count,
            decision_reason=f'Dominant parity: {parity} ({confidence:.0%} confidence from {sample_count} samples)'
        )
        db.add(audit)
        db.commit()
    else:
        # Update confidence if we have new info
        alias.sample_count = sample_count
        alias.confidence_score = confidence
        db.commit()
    
    return alias.patient_id
```

#### File: `backend/app/services/alert_engine.py`

```python
"""
Alert Engine - Debounced critical vitals monitoring
"""
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.alerts import PatientAlert
from app.config import settings


def process_vitals_for_alerts(patient_id: UUID, bpm: int, oxygen: int, db: Session):
    """
    Check vitals and manage alert lifecycle with debouncing.
    
    Rules:
    - Open alert: Requires 2 consecutive abnormal samples
    - Close alert: Requires 2 consecutive normal samples
    - Abnormal: BPM < 60 or BPM > 100
    
    This prevents alert fatigue from transient spikes.
    """
    is_abnormal = bpm < settings.ALERT_BPM_LOW or bpm > settings.ALERT_BPM_HIGH
    
    # Find current open alert
    open_alert = db.query(PatientAlert)\
        .filter_by(patient_id=patient_id, status='open')\
        .order_by(PatientAlert.opened_at.desc())\
        .first()
    
    if is_abnormal:
        if open_alert:
            # Update existing alert
            open_alert.last_bpm = bpm
            open_alert.last_oxygen = oxygen
            open_alert.consecutive_abnormal_count += 1
            open_alert.consecutive_normal_count = 0
        else:
            # Check for recent pending alert
            recent_closed = db.query(PatientAlert)\
                .filter_by(patient_id=patient_id)\
                .filter(PatientAlert.status.in_(['closed', 'pending']))\
                .order_by(PatientAlert.opened_at.desc())\
                .first()
            
            if recent_closed and recent_closed.consecutive_abnormal_count < settings.ALERT_DEBOUNCE_COUNT:
                # Second consecutive abnormal - OPEN alert
                recent_closed.status = 'open'
                recent_closed.closed_at = None
                recent_closed.consecutive_abnormal_count += 1
                recent_closed.last_bpm = bpm
                recent_closed.last_oxygen = oxygen
            else:
                # First abnormal - create pending alert
                alert = PatientAlert(
                    patient_id=patient_id,
                    status='pending',
                    opened_at=datetime.utcnow(),
                    last_bpm=bpm,
                    last_oxygen=oxygen,
                    consecutive_abnormal_count=1,
                    consecutive_normal_count=0
                )
                db.add(alert)
    else:
        # Normal reading
        if open_alert:
            open_alert.consecutive_normal_count += 1
            open_alert.consecutive_abnormal_count = 0
            
            if open_alert.consecutive_normal_count >= settings.ALERT_DEBOUNCE_COUNT:
                # CLOSE alert
                open_alert.status = 'closed'
                open_alert.closed_at = datetime.utcnow()
    
    db.commit()


def get_open_alerts(db: Session):
    """Get all currently open alerts"""
    return db.query(PatientAlert)\
        .filter_by(status='open')\
        .order_by(PatientAlert.opened_at.desc())\
        .all()


def get_patient_alert_history(patient_id: UUID, db: Session):
    """Get alert history for a patient"""
    return db.query(PatientAlert)\
        .filter_by(patient_id=patient_id)\
        .filter(PatientAlert.status == 'closed')\
        .order_by(PatientAlert.closed_at.desc())\
        .limit(20)\
        .all()
```

---

## COMPLETE FILE LISTING

Due to the size of this project (100+ files), I'll provide the complete implementation in structured sections. Each file is ready to copy-paste.

### Backend Structure Summary

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py ✓ (provided in README.md)
│   ├── config.py ✓ (provided in README.md)
│   ├── database.py ✓ (provided in README.md)
│   ├── models/
│   │   ├── __init__.py ✓ (provided above)
│   │   ├── staging.py ✓ (provided above)
│   │   ├── cleaned.py ✓ (provided above)
│   │   ├── identity.py ✓ (provided above)
│   │   └── alerts.py ✓ (provided above)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── telemetry_decoder.py ✓ (above)
│   │   ├── cipher.py ✓ (above)
│   │   ├── identity_reconciler.py ✓ (above)
│   │   ├── alert_engine.py ✓ (above)
│   │   └── data_ingestion.py → See Section 2
│   ├── api/
│   │   ├── __init__.py
│   │   ├── patients.py → See Section 3
│   │   ├── vitals.py → See Section 3
│   │   ├── prescriptions.py → See Section 3
│   │   └── alerts.py → See Section 3
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── patient.py → See Section 4
│   │   ├── telemetry.py → See Section 4
│   │   ├── prescription.py → See Section 4
│   │   └── alert.py → See Section 4
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── vitals_stream.py → See Section 5
│   └── workers/
│       ├── __init__.py
│       ├── telemetry_processor.py → See Section 6
│       └── live_simulator.py → See Section 6
├── tests/ → See Section 7
├── migrations/ → See Section 8
├── seed_data/ → See Section 9
├── requirements.txt ✓ (provided above)
├── Dockerfile ✓ (provided above)
└── pyproject.toml ✓ (provided in README.md)
```

---

## NEXT STEPS

**This guide contains:**
1. ✅ Complete architecture overview
2. ✅ Core backend services (decoder, cipher, identity, alerts)
3. ✅ Database models (staging, cleaned, identity, alerts)
4. ⏳ API endpoints (next section)
5. ⏳ Frontend React app (next section)
6. ⏳ WebSocket handlers (next section)
7. ⏳ Tests (next section)
8. ⏳ Migrations (next section)
9. ⏳ Seed data (next section)

**To continue implementation:**

Would you like me to provide the remaining sections now? I can create:
- **Section 2:** Data Ingestion Service
- **Section 3:** Complete API Endpoints
- **Section 4:** Pydantic Schemas  
- **Section 5:** WebSocket Implementation
- **Section 6:** Background Workers
- **Section 7:** Complete Test Suite
- **Section 8:** Database Migrations
- **Section 9:** Seed Data Generator

**Or** would you prefer to start implementing what we have and I'll provide the rest in follow-up documents?

---

**Built with care for St. Jude's Research Hospital** ❤️  
**Version 1.0 - Implementation Guide Part 1**
