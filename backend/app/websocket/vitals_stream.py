"""
WebSocket server for patient vitals streaming.

The telemetry processor runs independently from the FastAPI process, so this
endpoint watches database state and emits deltas instead of depending on
in-memory broadcast helpers.
"""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from app.config import settings
from app.database import SessionLocal

router = APIRouter()


def _get_patient_snapshot(patient_id: str) -> dict[str, Any] | None:
    db = SessionLocal()
    try:
        row = (
            db.execute(
                text(
                    """
                    SELECT
                        pa.patient_id,
                        cd.decoded_name AS patient_name,
                        latest_vitals.bpm AS last_bpm,
                        latest_vitals.oxygen AS last_oxygen,
                        latest_vitals.timestamp AS last_vitals_timestamp,
                        EXISTS(
                            SELECT 1
                            FROM patient_alerts
                            WHERE patient_alerts.patient_id = pa.patient_id
                              AND status = 'open'
                        ) AS has_active_alert
                    FROM patient_alias pa
                    LEFT JOIN clean_demographics cd
                        ON cd.patient_raw_id = pa.patient_raw_id
                    LEFT JOIN LATERAL (
                        SELECT bpm, oxygen, timestamp
                        FROM clean_telemetry ct
                        WHERE ct.patient_raw_id = pa.patient_raw_id
                          AND ct.parity_flag = pa.parity_flag
                          AND ct.quality_flag = 'good'
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ) latest_vitals ON true
                    WHERE pa.patient_id = :patient_id
                    """
                ),
                {"patient_id": patient_id},
            )
            .mappings()
            .first()
        )

        if row is None:
            return None

        snapshot = dict(row)
        timestamp = snapshot.get("last_vitals_timestamp")
        snapshot["last_vitals_timestamp"] = (
            timestamp.isoformat() if timestamp is not None else None
        )
        snapshot["has_active_alert"] = bool(snapshot.get("has_active_alert"))
        return snapshot
    finally:
        db.close()


def _has_vitals_changed(
    previous_snapshot: dict[str, Any] | None, current_snapshot: dict[str, Any]
) -> bool:
    if current_snapshot.get("last_vitals_timestamp") is None:
        return False

    if previous_snapshot is None:
        return True

    tracked_fields = ("last_vitals_timestamp", "last_bpm", "last_oxygen")
    return any(
        previous_snapshot.get(field) != current_snapshot.get(field)
        for field in tracked_fields
    )


def _build_vitals_message(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "vitals_update",
        "patient_id": str(snapshot["patient_id"]),
        "timestamp": snapshot["last_vitals_timestamp"],
        "bpm": snapshot["last_bpm"],
        "oxygen": snapshot["last_oxygen"],
    }


def _build_alert_message(
    previous_snapshot: dict[str, Any], current_snapshot: dict[str, Any]
) -> dict[str, Any] | None:
    if previous_snapshot.get("has_active_alert") == current_snapshot.get("has_active_alert"):
        return None

    if current_snapshot.get("has_active_alert"):
        return {
            "type": "alert_opened",
            "patient_id": str(current_snapshot["patient_id"]),
            "patient_name": current_snapshot.get("patient_name") or "Unknown",
            "last_bpm": current_snapshot.get("last_bpm"),
        }

    return {
        "type": "alert_closed",
        "patient_id": str(current_snapshot["patient_id"]),
    }


@router.websocket("/vitals/{patient_id}")
async def vitals_websocket_endpoint(websocket: WebSocket, patient_id: str):
    """
    WebSocket endpoint for patient vitals monitoring.

    The server emits vitals and alert deltas whenever database state changes.
    Clients may optionally send {"type": "ping"} heartbeats.
    """
    await websocket.accept()

    snapshot = await run_in_threadpool(_get_patient_snapshot, patient_id)
    if snapshot is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if _has_vitals_changed(None, snapshot):
        await websocket.send_json(_build_vitals_message(snapshot))

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WS_POLL_INTERVAL_SECONDS,
                )
                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    continue

                if message.get("type") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    )
            except asyncio.TimeoutError:
                current_snapshot = await run_in_threadpool(_get_patient_snapshot, patient_id)
                if current_snapshot is None:
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                    return

                if _has_vitals_changed(snapshot, current_snapshot):
                    await websocket.send_json(_build_vitals_message(current_snapshot))

                alert_message = _build_alert_message(snapshot, current_snapshot)
                if alert_message is not None:
                    await websocket.send_json(alert_message)

                snapshot = current_snapshot

    except WebSocketDisconnect:
        return
