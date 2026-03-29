# LAZARUS — Complete Implementation Plan

**Date:** 2026-03-29
**Current Status:** 54% complete (documentation + generator scripts only, no actual source files on disk)
**Goal:** Fully functional medical forensic recovery dashboard

---

## Current State Analysis

### What Exists (on disk, root level only)
| Category | Files | Notes |
|----------|-------|-------|
| Config | `docker-compose.yml`, `.env.example`, `.gitignore` | Ready to use |
| Documentation | 8 `.md` files | Complete specs |
| Generator Scripts | 17 `.py` files | Contain all code as inline strings, **never executed** |
| Other | `.zencoder/context.md` | Architecture reference |

### What Does NOT Exist
- `backend/` directory — **empty**
- `frontend/` directory — **empty**
- `nginx/` directory — **empty**
- No actual `.py`, `.ts`, `.tsx`, `.json` source files anywhere

### Generator Script Inventory
| Script | Lines | Scope | Status |
|--------|-------|-------|--------|
| `BUILD_LAZARUS.py` | 713 | Backend core (config, DB, models, partial services) | Partial — says "Part 2 needed" |
| `BUILD_COMPLETE.py` | 470 | Backend core (config, DB, models) | Partial — says "Part 2 needed" |
| `GENERATE_ALL_FILES.py` | 256 | Nginx + backend skeleton | Partial — only basics |
| `SETUP_FRONTEND.py` | 546 | Full frontend foundation (15 files) | **Complete** |
| `create_migrations.py` | 499 | Alembic config + migrations | **Complete** |
| `CREATE_MIGRATIONS_COMPLETE.py` | 609 | Full migration setup with dirs | **Complete** |
| `setup_seed_data.py` | 673 | Seed data generator + loader | **Complete** |
| `create_structure.py` | 54 | Directory creation only | **Complete** |

---

## Implementation Plan — 7 Phases

### PHASE 0: Project Structure Setup (5 min)
**Goal:** Create all directories

Run `create_structure.py` to scaffold the directory tree:
```
nginx/
backend/app/models/
backend/app/schemas/
backend/app/api/
backend/app/websocket/
backend/app/services/
backend/app/utils/
backend/app/workers/
backend/tests/
backend/migrations/versions/
backend/seed_data/
frontend/src/api/
frontend/src/components/
frontend/src/pages/
frontend/src/hooks/
frontend/src/types/
frontend/src/styles/
frontend/public/
```

**Command:**
```bash
python create_structure.py
```

---

### PHASE 1: Backend Core Generation (15 min)
**Goal:** Generate all backend source files

The existing generators are incomplete individually. Strategy: run `BUILD_LAZARUS.py` for the partial backend it covers, then manually create the remaining files using code from `IMPLEMENTATION_GUIDE_COMPLETE.md` and `IMPLEMENTATION_GUIDE_PART2.md`.

#### Step 1.1: Run `BUILD_LAZARUS.py`
Generates (from its `FILES` dict):
- `backend/requirements.txt`
- `backend/Dockerfile`
- `backend/.dockerignore`
- `backend/app/__init__.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/models/staging.py`
- `backend/app/models/cleaned.py`
- `backend/app/models/identity.py`
- `backend/app/models/alerts.py`
- `backend/app/services/__init__.py`
- `backend/app/services/telemetry_decoder.py`
- `backend/app/services/cipher.py`
- `nginx/nginx.conf`

**Command:**
```bash
python BUILD_LAZARUS.py
```

#### Step 1.2: Create Missing Backend Files

These files are documented in `IMPLEMENTATION_GUIDE_COMPLETE.md` and `IMPLEMENTATION_GUIDE_PART2.md` but not in any generator. Create them manually:

**Services (2 files):**
- `backend/app/services/identity_reconciler.py` — BPM parity reconciliation
- `backend/app/services/alert_engine.py` — Debounced alert logic

**API (4 files):**
- `backend/app/api/__init__.py`
- `backend/app/api/patients.py` — Patient list/detail endpoints
- `backend/app/api/vitals.py` — Time-series vitals endpoint
- `backend/app/api/prescriptions.py` — Medication decryption display
- `backend/app/api/alerts.py` — Alert management endpoints

**Schemas (5 files):**
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/patient.py`
- `backend/app/schemas/telemetry.py`
- `backend/app/schemas/prescription.py`
- `backend/app/schemas/alert.py`

**WebSocket (2 files):**
- `backend/app/websocket/__init__.py`
- `backend/app/websocket/vitals_stream.py` — Real-time streaming

**Update `backend/app/main.py`** to include all routers (patients, vitals, prescriptions, alerts, websocket).

---

### PHASE 2: Database Migrations (10 min)
**Goal:** Alembic setup + initial migration

#### Step 2.1: Run `CREATE_MIGRATIONS_COMPLETE.py`
Generates:
- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/versions/001_initial_schema.py`
- `backend/migrations/versions/002_create_patient_view.py`

**Command:**
```bash
python CREATE_MIGRATIONS_COMPLETE.py
```

#### Step 2.2: Verify Migration Files
- Check `alembic.ini` has correct `sqlalchemy.url`
- Check `env.py` imports all models from `app.models`
- Check initial migration creates all 7 tables + 1 materialized view

---

### PHASE 3: Seed Data Generator (10 min)
**Goal:** Synthetic data for 20 patients

#### Step 3.1: Run `setup_seed_data.py`
Generates:
- `backend/seed_data/generate_seeds.py` — Creates 3 CSV files
- `backend/seed_data/load_seeds.py` — Loads CSVs into DB + runs ETL

**Command:**
```bash
python setup_seed_data.py
```

#### Step 3.2: Verify Seed Files
- `generate_seeds.py` should produce:
  - `patient_demographics.csv` (20 patients, 5 with colliding IDs)
  - `telemetry_logs.csv` (20,000 samples — 1000 per patient)
  - `prescription_audit.csv` (3-8 meds per patient, age-encrypted)

---

### PHASE 4: Frontend Generation (15 min)
**Goal:** Complete React + TypeScript frontend

#### Step 4.1: Run `SETUP_FRONTEND.py`
Generates 15 files:
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/tailwind.config.js`
- `frontend/postcss.config.js`
- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/api/websocket.ts`
- `frontend/src/types/index.ts`
- `frontend/src/styles/index.css`
- `frontend/src/components/Dashboard.tsx` (placeholder)
- `frontend/src/components/PatientDetail.tsx` (placeholder)

**Command:**
```bash
python SETUP_FRONTEND.py
```

#### Step 4.2: Install Frontend Dependencies
```bash
cd frontend && npm install
```

#### Step 4.3: Build Missing Frontend Components (the big piece)
These are NOT in any generator script. Must be written from scratch:

**Pages (2 files):**
- `frontend/src/pages/Dashboard.tsx` — 4-panel layout (alerts banner, patient cards, vitals chart, pharmacy table)
- `frontend/src/pages/PatientDetail.tsx` — Individual patient deep-dive

**Components (5 files):**
- `frontend/src/components/PatientCard.tsx` — Name, age, ward, last BPM/O2, alert badge
- `frontend/src/components/VitalsChart.tsx` — Recharts time-series (BPM + SpO2 with safe zone bands)
- `frontend/src/components/PharmacyTable.tsx` — Encrypted vs decrypted med names
- `frontend/src/components/AlertBanner.tsx` — Global critical alerts strip
- `frontend/src/components/Layout.tsx` — App shell with nav

**Hooks (5 files):**
- `frontend/src/hooks/usePatients.ts` — Fetch patient list via TanStack Query
- `frontend/src/hooks/useVitals.ts` — Fetch + subscribe to vitals time-series
- `frontend/src/hooks/usePrescriptions.ts` — Fetch prescriptions
- `frontend/src/hooks/useAlerts.ts` — Fetch + subscribe to alerts
- `frontend/src/hooks/useWebSocket.ts` — WebSocket connection management

**Pages directory setup:**
- Create `frontend/src/pages/` directory
- Update `frontend/src/App.tsx` routing to use pages instead of components

---

### PHASE 5: Backend Workers (10 min)
**Goal:** Background data processing + live simulator

Create manually (not in any generator):

- `backend/app/workers/__init__.py`
- `backend/app/workers/telemetry_processor.py` — Continuously processes staging → cleaned
- `backend/app/workers/live_simulator.py` — Generates fake telemetry every 5 seconds for demo

These are referenced in `PROJECT_STATUS.md` and `README.md` but code must be written.

---

### PHASE 6: Tests (30 min)
**Goal:** Unit + integration test suite

Create manually:

- `backend/tests/__init__.py`
- `backend/tests/test_telemetry_decoder.py` — Test hex decode/encode, edge cases, invalid input
- `backend/tests/test_cipher.py` — Test encrypt/decrypt roundtrip, known examples
- `backend/tests/test_identity_reconciler.py` — Test parity logic, confidence scoring
- `backend/tests/test_alert_engine.py` — Test debouncing, open/close lifecycle
- `backend/tests/test_api_endpoints.py` — Integration tests for all REST endpoints

---

### PHASE 7: Integration & Verification (30 min)
**Goal:** End-to-end working system

#### Step 7.1: Docker Compose Up
```bash
copy .env.example .env
docker-compose up -d
docker-compose ps  # Wait for all healthy
```

#### Step 7.2: Run Migrations
```bash
docker-compose exec backend alembic upgrade head
```

#### Step 7.3: Generate & Load Seed Data
```bash
docker-compose exec backend python seed_data/generate_seeds.py
docker-compose exec backend python seed_data/load_seeds.py
```

#### Step 7.4: Start Live Simulator
```bash
docker-compose exec backend python app/workers/live_simulator.py
```

#### Step 7.5: Verify
- Backend health: `curl http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`
- WebSocket: Connect to `ws://localhost:8000/ws/vitals/{patient_id}`

#### Step 7.6: Run Tests
```bash
docker-compose exec backend pytest --cov=app --cov-report=html
cd frontend && npm test
```

---

## Execution Order Summary

```
Phase 0: python create_structure.py           (5 min)
Phase 1: python BUILD_LAZARUS.py              (15 min)
         + write 18 missing backend files
Phase 2: python CREATE_MIGRATIONS_COMPLETE.py (10 min)
Phase 3: python setup_seed_data.py            (10 min)
Phase 4: python SETUP_FRONTEND.py             (15 min)
         + npm install
         + write 12 missing frontend files
Phase 5: write 3 worker files                 (10 min)
Phase 6: write 6 test files                   (30 min)
Phase 7: docker-compose up + verify           (30 min)
```

**Total estimated time: 2.5-3 hours**

---

## File Count Summary

| Category | Existing (in generators) | Need to Create | Total |
|----------|-------------------------|----------------|-------|
| Backend Core | 10 | 0 | 10 |
| Backend Services | 2 | 2 | 4 |
| Backend API | 0 | 5 | 5 |
| Backend Schemas | 0 | 5 | 5 |
| Backend WebSocket | 0 | 2 | 2 |
| Backend Workers | 0 | 3 | 3 |
| Backend Tests | 0 | 6 | 6 |
| Backend Migrations | 4 | 0 | 4 |
| Backend Seed Data | 2 | 0 | 2 |
| Frontend Config | 7 | 0 | 7 |
| Frontend App | 5 | 0 | 5 |
| Frontend Components | 2 | 5 | 7 |
| Frontend Pages | 0 | 2 | 2 |
| Frontend Hooks | 0 | 5 | 5 |
| Nginx | 1 | 0 | 1 |
| **TOTAL** | **33** | **35** | **68** |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Generator scripts have bugs | Medium | Test each script output before proceeding |
| Missing frontend components | High | Most complex remaining work — allocate 40% of time |
| Docker networking issues | Low | All services on `lazarus-network` bridge |
| PostgreSQL schema mismatch | Medium | Use Alembic autogenerate to validate |
| WebSocket connection failures | Low | Nginx config already handles WS proxy |

---

## Key Files Reference

All code for missing files is available in these documents:
- `IMPLEMENTATION_GUIDE_COMPLETE.md` — Services, models code
- `IMPLEMENTATION_GUIDE_PART2.md` — API endpoints, schemas, WebSocket code
- `QUICK_COMPLETION_GUIDE.md` — Seed data, migrations code
- `FRONTEND_FOUNDATION_COMPLETE.md` — Frontend architecture spec
- `README.md` — Full system spec with algorithms
- `.zencoder/context.md` — Deep architecture rationale

---

**Plan Version:** 1.0
**Ready to execute:** Yes
