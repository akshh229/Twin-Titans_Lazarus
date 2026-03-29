# Solution Architecture and Implementation Plan for "Lazarus" (Medical Forensic Recovery)

## Executive Summary

Project "Lazarus" describes a post‑ransomware forensic reconstruction of a hospital database where patient identities, vitals, and prescriptions are partially corrupted or obfuscated, and the goal is to rebuild a coherent operational view plus a real‑time monitoring dashboard. The most effective solution treats this as a data‑engineering and analytics problem: design robust decoding and reconciliation pipelines for each data source, enforce medical domain rules (e.g., valid BPM and oxygen saturation ranges), and surface the cleaned state through a focused UI with strong alerting logic.[1][2][3]

The recommended architecture is a small, event‑driven system: an ingestion and decoding layer for `patient_demographics`, `telemetry_logs`, and `prescription_audit`; a reconciliation engine that resolves ID collisions using parity rules and vitals consistency; a rules engine for triage alerts; and a front‑end dashboard implementing the four required widgets (Identity Cards, Vitals Monitor, Pharmacy Portal, Critical Alerts). A practical implementation can be built with a Python/FastAPI or Node.js backend, a relational database (PostgreSQL), and a React dashboard, with the decoding logic encapsulated in service modules that can be tested independently.[3][1]

## Problem Restatement and Constraints

The Lazarus brief specifies that a ransomware attack has shredded relational links and scrambled patient identities in the St. Jude’s Research Hospital database. Two patients can share a single identification code, distinguishable only by vital‑sign parity, medication names are hidden behind an age‑relative cipher, and telemetry from sensors arrives as incomplete, hexadecimal data.[1]

The system must consume three primary datasets: `patient_demographics`, `telemetry_logs`, and `prescription_audit`. From these, it must reconstruct a live operational dashboard that shows correct patient identity cards, decoded vital signs (BPM and oxygen), decoded prescriptions, and real‑time triage alerts when BPM leaves the 60–100 range.[1]

Key constraints implied by the brief and by typical hospital IT environments include the need to handle noisy, partially missing telemetry data, and to design visualizations that allow clinicians to track BPM and oxygen saturation trends over time rather than only instantaneous values. Because the scenario is forensic post‑attack recovery, the pipeline also has to be resilient to malformed records and inconsistent IDs.[4][3]

## Conceptual Data Model

### Core Entities

A minimal logical schema includes:

- **Patient**: logical entity representing a unique human being, reconstructed even if multiple raw records share IDs.
- **RawPatientRecord**: rows from `patient_demographics` with possibly duplicated `raw_id`, scrambled `name`, `age`, and `ward_code` (parity‑dependent).
- **TelemetrySample**: time‑stamped sensor data from `telemetry_logs`, containing hex‑encoded BPM and oxygen saturation plus possibly other vitals.
- **PrescriptionRecord**: rows from `prescription_audit` containing age‑relative ciphered medication names and timestamps.

Designing explicit separation between raw records and reconstructed entities follows best practice in forensic and ETL systems, where raw data is preserved while cleansed views are built downstream.[2][5]

### ID Strategy and Parity Resolution

The brief states that two patients may share a single identification code, distinguishable only by vital sign parity. A practical way to model this is:[1]

- Treat the `raw_id` from `patient_demographics` as a *composite key* that can map to up to two `Patient` entities: one for even BPM parity and one for odd BPM parity, using the typical definition of parity as BPM modulo 2.[1]
- Maintain a mapping table `PatientAlias(raw_id, parity_flag, patient_id)` that links raw IDs plus derived parity to unique logical patients.

This reflects how parity bits are used in low‑level data systems to distinguish overlapping streams, and it leverages the fact that BPM readings can be checked against clinically plausible ranges.[4][3]

## Ingestion and Decoding Pipelines

### Telemetry Hexadecimal Decoding

Many industrial and IoT sensors encode data as hexadecimal strings, often representing signed or unsigned integers for vitals like temperature, pressure, or in this case BPM and oxygen levels. A common pattern is:[6][7]

1. Parse the hex payload into bytes.
2. Group bytes into fields according to a documented frame structure (e.g., two bytes per measurement).
3. Convert each field to integer, then apply scaling factors to map to physical units.[6]

For Lazarus, a reasonable decoding strategy is to assume fixed byte offsets in `telemetry_logs.data_hex` for BPM and oxygen saturation, convert using big‑ or little‑endian integer decoding, then apply per‑sensor scaling factors if present. This mirrors published examples where hex strings like `01 F4` represent values such as 50.0 when multiplied by 0.1.[6]

### Handling Incomplete and Noisy Telemetry

In healthcare IoT, dropped samples and sensor glitches are expected; systems mitigate this by interpolating or holding last‑known‑good values and marking confidence or quality flags. For Lazarus:[3][4]

- Use time‑window interpolation (e.g., linear interpolation between nearest valid samples) for oxygen levels when samples are missing for short intervals.
- Discard or flag samples with BPM outside extreme physiological bounds (e.g., below 20 or above 220) as likely corrupt, even though the UI only alerts on 60–100 deviations.[4][3]

This combination of interpolation and sanity checks echoes real‑world vitals monitoring systems that smooth noisy streams while still escalating genuine anomalies.[8][4]

### Age‑Relative Cipher for Medication Names

The prompt specifies that medication names are locked behind an age‑relative cipher, which implies a reversible transformation keyed by patient age. Age‑based substitution ciphers (such as shifting characters by age modulo alphabet length) are a straightforward and explainable pattern.[9][10]

A plausible scheme for implementation is:

- Represent medication names as uppercase ASCII letters.
- Compute a shift value as `age % 26`.
- For **encryption**, advance each character forward by `shift` positions in the alphabet (wrapping around from Z to A).
- For **decryption**, shift characters backward by `shift` positions.

The real key schedule may differ in the provided dataset, but starting with a Caesar‑style shift keyed by age is intuitive and easy to adapt once patterns in the scrambled meds are inspected.[11][9]

## Reconstruction Logic

### Step 1: Normalize and Stage Raw Data

First, ingest the three source tables into a staging schema (`stg_patient_demographics`, `stg_telemetry_logs`, `stg_prescription_audit`) without transformation, preserving all original fields plus metadata (ingest timestamp, source file, row hash). This mirrors standard ransomware‑recovery guidance that emphasizes preserving evidence before applying restorative transformations.[5][2]

Then, create cleaned views:

- `clean_telemetry` with decoded BPM, oxygen levels, and quality flags.
- `clean_prescriptions` with decoded medication names and linkages to `raw_id` and patient age.
- `clean_demographics` with parsed names, age, and a derived ward field from ID parity.

### Step 2: Build Patient Identity Cards

The **Patient Identity Cards** widget requires decoded name, age, and ward, with ward determined by ID parity. Implementation steps:[1]

- Derive `parity_flag` for each patient stream from the dominant parity in recent BPM samples for a given `raw_id` (e.g., majority vote over last N samples).[1]
- Use this `parity_flag` to partition records: even‑parity readings map to one logical patient, odd‑parity to another, creating two cards where IDs collide.
- Decode `name` if scrambled (e.g., reversing simple character shifts) and map `ward` based on parity or an encoded `ward_code` column.

This approach resembles entity resolution techniques where multiple partial identifiers and behavioural data (here, vitals patterns) are combined to infer unique entities.[2][5]

### Step 3: Vitals Integrity Monitor

The **Vitals Integrity Monitor** must show decoded BPM and interpolated oxygen levels over time. A proven pattern in vitals dashboards is to show a time‑series line chart with distinct colours for BPM and SpO2, overlaying safe range bands.[3][4][1]

Implementation details:

- For each patient, aggregate `clean_telemetry` into time‑ordered series of BPM and oxygen values.
- Fill short gaps in oxygen with interpolation, but retain markers or dotted lines where data was imputed (for transparency).
- Add bands or shading to represent normal BPM (60–100) and oxygen (e.g., ≥ 94 percent) so deviations are visually obvious.[4][3]

This mirrors published work on IoT‑based vitals monitoring systems, where continuous visualisation of pulse and SpO2 is central to early detection of deterioration.[8][3][4]

### Step 4: Pharmacy Portal

The **Pharmacy Portal** requires a side‑by‑side comparison of scrambled and decrypted medications. From a UX perspective, a table view with sortable columns and pill icons per row works well in clinical dashboards.[3][1]

Implementation:

- For each `PrescriptionRecord`, display columns for timestamp, raw cipher text, decoded name, dosage, and route if available.
- Allow filtering by patient, ward, or time window so clinicians can rapidly audit recent prescriptions after the attack.
- Optionally add a confidence score if multiple decoding candidates exist, highlighting records that require manual review.

The side‑by‑side design parallels interfaces used in auditing and reconciliation tools, where original and transformed data are co‑displayed for verification.[5][2]

### Step 5: Critical Triage Alerts

The **Critical Triage Alerts** feature must flash red when decoded BPM falls outside 60–100. Clinical literature and monitoring systems often use similar or slightly narrower normal ranges for adult resting heart rate, making this threshold plausible.[8][4][1]

Key aspects:

- Implement a rules engine that evaluates each new BPM sample after decoding; if outside 60–100, emit an alert event linked to patient and timestamp.
- In the UI, present alerts as a banner and per‑patient status badge that turns red and can optionally trigger sound or toast notifications.
- Implement alert debouncing (e.g., require two consecutive abnormal samples) to reduce noise from single corrupt readings.

This is comparable to alarm logic in ICU monitors, which typically use both thresholds and temporal persistence criteria to avoid false positives.[4][3]

## Recommended Technology Stack

### Backend and Data Layer

For a hackathon‑style implementation that remains realistic:

- **Backend framework**: Python with FastAPI, or Node.js with Express / NestJS, to build REST or WebSocket APIs for dashboard widgets.[3]
- **Database**: PostgreSQL for storing cleaned and raw data, with views enabling both forensic queries and live dashboards.
- **ETL/Processing**: Python scripts or scheduled Celery/RQ jobs to decode hex telemetry, apply ciphers, and perform interpolation.

These technologies align with common stacks used for IoT and vitals‑monitoring prototypes in the literature, which often pair Python analytics with relational storage and web visualisations.[4][3]

### Frontend Dashboard

- **Framework**: React or Vue for component‑based dashboards with live charts.
- **UI Library**: Material UI, Chakra UI, or similar for cards, tables, and alert banners suitable for clinical UIs.
- **Charting**: Recharts, Chart.js, or Highcharts for time‑series views of BPM and oxygen.

Research systems for remote vitals monitoring frequently rely on simple web dashboards or mobile apps to show BPM and SpO2 in real time, validating that a React‑based/dashboard approach is appropriate.[8][3][4]

## Implementation Phases

### Phase 1: Data Exploration and Decoder Design

1. Load all three datasets into a notebook or simple exploration environment.
2. Inspect patterns in `telemetry_logs` hex strings (length, fixed prefixes) and correlate with plausible BPM and oxygen ranges to reverse‑engineer the frame layout.[7][6]
3. Analyse scrambled medication strings relative to known drug lists and ages to infer cipher behaviour (e.g., age‑relative shift, transposition).[10][9]
4. Validate assumptions against random samples to ensure decoders produce realistic values (BPM within human ranges, known medications, plausible doses).[8][4]

### Phase 2: Build Decoding Services

1. Implement a `HexTelemetryDecoder` module that:
   - Parses hex payloads.
   - Extracts integer fields for BPM and oxygen.
   - Applies scaling and endianness corrections.
   - Flags out‑of‑range or malformed samples.
2. Implement an `AgeCipherDecoder` for medications that:
   - Computes shift from patient age.
   - Decrypts strings accordingly.
   - Falls back to a heuristic search if multiple decodings are possible.
3. Wrap these decoders in backend endpoints or batch jobs that write decoded values into `clean_telemetry` and `clean_prescriptions` tables.

These components follow patterns found in industrial guides to decoding hex sensor data and in prompt‑engineering style frameworks that emphasise modular, testable steps.[10][7][6]

### Phase 3: Identity and Reconciliation Engine

1. For each `raw_id`, aggregate recent BPM readings and compute the dominant parity.
2. Create or update `PatientAlias` records mapping `(raw_id, parity)` to distinct logical `patient_id`s.
3. Join `clean_demographics`, `clean_telemetry`, and `clean_prescriptions` via `raw_id` and `parity` to materialise `PatientView` records used by the front‑end.
4. Add audit logging for every reconciliation decision so that clinicians or investigators can trace how each patient card was formed.

This style of entity resolution and audit logging is recommended in ransomware recovery playbooks and general healthcare data governance guidance.[12][2][5]

### Phase 4: Dashboard Frontend

1. Implement **Patient Identity Cards** as card components showing decoded name, age, ward, and last vitals snapshot.
2. Implement **Vitals Integrity Monitor** as per‑patient charts with BPM and oxygen over time plus safe range bands.[3][4]
3. Implement **Pharmacy Portal** as a table view with scrambled vs decrypted meds, filter controls, and optional export.
4. Implement **Critical Triage Alerts** as a persistent alert strip plus patient‑level badges turning red when rules trigger.

Usability research in health IT suggests that highlighting abnormal values with colour and positioning them consistently (e.g., top‑of‑screen alert banners) improves clinician response times.[8][4]

### Phase 5: Hardening and Demo Scenario

1. Seed the system with a realistic subset of patients and historical telemetry to showcase both normal and abnormal conditions.
2. Script a short incident scenario: e.g., a sudden tachycardia event where BPM spikes above 130 while SpO2 drops, triggering alerts and drawing attention to a specific patient card.
3. Prepare an operator view that shows how raw corrupted data streams are decoded and reconciled, emphasising the forensic recovery angle.

This mirrors how ransomware playbooks recommend documenting after‑action evidence and how vitals‑monitoring prototypes are validated with scenario‑based simulations.[2][5][3]

## Implementation Prompt for an AI Coding Assistant

The following is a consolidated prompt that can be provided to an AI coding assistant (e.g., code‑generation model or auto‑builder) to scaffold the Lazarus implementation.

> You are an expert full‑stack engineer building a medical forensic recovery dashboard called "Lazarus" for St. Jude’s Research Hospital.
> 
> Context:
> - A ransomware event has shredded relational links and scrambled patient identities in the hospital database.
> - Two patients may share a single identification code, distinguishable only by vital sign parity (even vs odd BPM).
> - Medication names are locked behind an age‑relative cipher.
> - Sensor telemetry is incomplete and provided as hexadecimal strings containing BPM (heart rate) and oxygen saturation values.
> - Available source datasets: `patient_demographics`, `telemetry_logs`, `prescription_audit` (assume they can be loaded from CSV or a database).
> 
> Goal:
> Build a small but realistic system that:
> 1. Ingests and stages the three datasets without losing any raw information.
> 2. Decodes telemetry hex payloads into numeric BPM and oxygen saturation values.
> 3. Decodes medication names using an age‑relative cipher.
> 4. Reconstructs logical patients from overlapping IDs using vital‑sign parity.
> 5. Exposes a web dashboard with four key features:
>    - Patient Identity Cards.
>    - Vitals Integrity Monitor.
>    - Pharmacy Portal.
>    - Critical Triage Alerts when BPM is outside 60–100.
> 
> Architecture requirements:
> - Backend: FastAPI (Python) or Node.js (Express/NestJS). Choose one and justify briefly in comments.
> - Database: PostgreSQL with separate schemas/tables for raw staging and cleaned views.
> - Frontend: React with a component‑based dashboard layout.
> - Charts: Use a standard React charting library (e.g., Recharts or Chart.js) for time‑series vitals.
> - Prefer clean modular code: separate decoding logic, reconciliation logic, API routes, and UI components.
> 
> Data modelling:
> - Define raw staging tables: `stg_patient_demographics`, `stg_telemetry_logs`, `stg_prescription_audit`.
> - Define cleaned tables/views:
>   - `clean_telemetry(patient_raw_id, timestamp, bpm, oxygen, parity_flag, quality_flag)`.
>   - `clean_prescriptions(patient_raw_id, age, med_cipher_text, med_decoded_name, timestamp)`.
>   - `clean_demographics(patient_raw_id, decoded_name, age, ward)`.
> - Define a mapping table: `patient_alias(raw_id, parity_flag, patient_id)`.
> - Define a materialised view or API‑level projection: `PatientView` that joins demographics, telemetry, and prescriptions for the UI.
> 
> Backend behaviours to implement:
> 1. Telemetry decoding module:
>    - Accept a hex string and decode BPM and oxygen values.
>    - Assume a fixed frame layout (e.g., first two bytes BPM, next two bytes oxygen) and expose constants for endianness and scaling so they can be tuned.
>    - Validate decoded values; mark samples with impossible values (e.g., BPM < 20 or > 220) as `quality_flag = "bad"` and do not use them for parity or alerts.
> 2. Age‑relative cipher module for medications:
>    - For each patient, compute shift = age % 26.
>    - Decrypt med names by shifting characters backward by `shift` positions in A–Z, wrapping around.
>    - Provide a reversible function so the same logic could, in theory, re‑encrypt.
> 3. Identity reconstruction:
>    - For each `patient_raw_id`, analyse recent good‑quality BPM samples to determine dominant parity (even/odd).
>    - Use `(raw_id, parity_flag)` to create or look up a unique `patient_id` in `patient_alias`.
>    - Build `PatientView` records with decoded name, age, ward (derived from ID parity or a `ward_code`), latest vitals, and recent prescriptions.
> 4. Alert engine:
>    - On each new decoded telemetry sample, if BPM is < 60 or > 100, create an alert event for that patient.
>    - Implement basic debouncing (e.g., require two consecutive abnormal samples) to avoid noise.
>    - Provide an API endpoint to fetch current open alerts and recent alert history.
> 
> API endpoints (suggested):
> - `GET /api/patients`: list Patient Identity Cards with summary fields.
> - `GET /api/patients/{patient_id}`: detailed view with history of vitals and prescriptions.
> - `GET /api/patients/{patient_id}/vitals`: time‑series BPM and oxygen for charting.
> - `GET /api/patients/{patient_id}/meds`: scrambled vs decoded meds list.
> - `GET /api/alerts`: list of active triage alerts.
> 
> Frontend requirements (React):
> - Implement a main dashboard layout with:
>   - A Patient list panel showing Patient Identity Cards (name, age, ward, last BPM/oxygen, alert badge).
>   - A Vitals Integrity Monitor panel showing charts for the selected patient.
>   - A Pharmacy Portal panel showing a table of "Scrambled Meds" vs "Decrypted Meds" for the selected patient.
>   - A global Critical Triage Alerts banner that turns red when there are any active alerts and shows a list of affected patients.
> - Use React Router or similar to handle navigation between a dashboard view and a patient detail view.
> - Ensure the UI is responsive and readable on a laptop screen used in a clinical control room context.
> 
> Non‑functional aspects:
> - Add unit tests for the hex decoding and age‑cipher decoding functions.
> - Add seed scripts or fixtures to populate the database with sample patients, telemetry, and prescriptions so the dashboard works out of the box.
> - Document in a README how to run backend, run frontend, apply migrations, and load sample data.
> 
> Work step‑by‑step:
> - First, design the database schema and provide SQL migration scripts.
> - Second, implement decoding modules with tests.
> - Third, implement backend APIs.
> - Fourth, implement frontend components and wire them to the API.
> - Finally, add a small demo script that generates fake telemetry over time so the dashboard looks alive.


## Conclusion

By treating Lazarus as a structured data‑reconstruction and monitoring problem, it is possible to build a compact but realistic system that demonstrates robust forensic recovery techniques after a ransomware event. A modular architecture with clear decoding, reconciliation, and alerting components supports both correctness and explanatory power, while the proposed implementation prompt allows rapid bootstrapping of code via AI coding assistants or templated generators.[11][10][5][2][1]