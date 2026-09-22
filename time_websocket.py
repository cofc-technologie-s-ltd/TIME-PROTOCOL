import asyncio
import json
from typing import List
from fastapi import WebSocket

class WebSocketConnectionManager:
    """
    Real-time event streaming connection manager for TIME Protocol.
    Broadcasts live consensus commits, ledger state transitions, and node health
    to subscribed custodial exchanges and WebSocket clients.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_event(self, event_type: str, data: dict):
        message = json.dumps({"event": event_type, "payload": data})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)
