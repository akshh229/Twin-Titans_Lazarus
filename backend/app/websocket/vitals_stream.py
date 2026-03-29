"""
WebSocket Server for Real-Time Vitals Streaming
Broadcasts vitals updates and alerts to connected clients
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from uuid import UUID
from datetime import datetime
import json

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, patient_id: str):
        await websocket.accept()
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = set()
        self.active_connections[patient_id].add(websocket)

    def disconnect(self, websocket: WebSocket, patient_id: str):
        if patient_id in self.active_connections:
            self.active_connections[patient_id].discard(websocket)
            if not self.active_connections[patient_id]:
                del self.active_connections[patient_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast_to_patient(self, message: dict, patient_id: str):
        if patient_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[patient_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            for conn in disconnected:
                self.active_connections[patient_id].discard(conn)


manager = ConnectionManager()


@router.websocket("/vitals/{patient_id}")
async def vitals_websocket_endpoint(websocket: WebSocket, patient_id: str):
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
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": str(datetime.utcnow())}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, patient_id)


async def broadcast_vitals_update(
    patient_id: str, bpm: int, oxygen: int, timestamp: datetime
):
    """Called by telemetry processor to broadcast new vitals."""
    message = {
        "type": "vitals_update",
        "patient_id": str(patient_id),
        "timestamp": timestamp.isoformat(),
        "bpm": bpm,
        "oxygen": oxygen,
    }
    await manager.broadcast_to_patient(message, patient_id)


async def broadcast_alert_opened(patient_id: str, patient_name: str, bpm: int):
    """Broadcast alert opened event"""
    message = {
        "type": "alert_opened",
        "patient_id": str(patient_id),
        "patient_name": patient_name,
        "last_bpm": bpm,
    }
    await manager.broadcast_to_patient(message, patient_id)


async def broadcast_alert_closed(patient_id: str):
    """Broadcast alert closed event"""
    message = {"type": "alert_closed", "patient_id": str(patient_id)}
    await manager.broadcast_to_patient(message, patient_id)
