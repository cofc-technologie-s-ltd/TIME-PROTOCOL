"""
TIME Protocol - WebSocket Connection Manager
Pure stdlib implementation (no external dependencies).
"""

import asyncio
import json
import time
from typing import Dict, Set, Any, Optional


class WebSocketConnection:
    """Represents a single WebSocket connection."""

    def __init__(self, connection_id: str, reader=None, writer=None):
        self.connection_id = connection_id
        self.reader = reader
        self.writer = writer
        self.connected_at = time.time()
        self.subscriptions: Set[str] = set()
        self.last_ping = time.time()

    def to_dict(self) -> dict:
        return {
            "connection_id": self.connection_id,
            "connected_at": self.connected_at,
            "subscriptions": list(self.subscriptions),
            "last_ping": self.last_ping,
        }


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time TIME Protocol updates.

    Pure stdlib implementation. No fastapi, no websockets library required.
    Can be upgraded to use the `websockets` package if available.
    """

    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.active_connections = self.connections  # alias for test compat
        self.subscriptions: Dict[str, Set[str]] = {
            "blocks": set(),
            "transactions": set(),
            "telemetry": set(),
            "mining": set(),
        }
        self._counter = 0

    def register(self, reader=None, writer=None) -> str:
        """Register a new connection. Returns connection ID."""
        self._counter += 1
        conn_id = f"conn_{self._counter}_{int(time.time() * 1000)}"
        conn = WebSocketConnection(conn_id, reader, writer)
        self.connections[conn_id] = conn
        return conn_id

    def unregister(self, connection_id: str) -> bool:
        """Remove a connection."""
        if connection_id not in self.connections:
            return False

        conn = self.connections.pop(connection_id)

        # Remove from all subscriptions
        for topic_conns in self.subscriptions.values():
            topic_conns.discard(connection_id)

        return True

    def subscribe(self, connection_id: str, topic: str) -> bool:
        """Subscribe a connection to a topic."""
        if connection_id not in self.connections:
            return False

        topic = topic.lower()
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()

        self.subscriptions[topic].add(connection_id)
        self.connections[connection_id].subscriptions.add(topic)
        return True

    def unsubscribe(self, connection_id: str, topic: str) -> bool:
        """Unsubscribe from a topic."""
        if connection_id not in self.connections:
            return False

        topic = topic.lower()
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)

        self.connections[connection_id].subscriptions.discard(topic)
        return True

    async def broadcast(self, topic: str, message: Dict[str, Any]) -> int:
        """Broadcast a message to all subscribers of a topic."""
        topic = topic.lower()
        if topic not in self.subscriptions:
            return 0

        payload = json.dumps({
            "topic": topic,
            "timestamp": time.time(),
            "data": message,
        })

        sent_count = 0
        for conn_id in list(self.subscriptions[topic]):
            conn = self.connections.get(conn_id)
            if not conn or not conn.writer:
                continue
            try:
                conn.writer.write(payload.encode())
                await conn.writer.drain()
                sent_count += 1
            except Exception:
                # Connection broken - clean up
                self.unregister(conn_id)

        return sent_count

    def broadcast_sync(self, topic: str, message: Dict[str, Any]) -> int:
        """Synchronous broadcast (for use from non-async code)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(topic, message))
                return len(self.subscriptions.get(topic.lower(), set()))
            return loop.run_until_complete(self.broadcast(topic, message))
        except RuntimeError:
            return 0

    def notify_new_block(self, block) -> int:
        """Notify all subscribers of a new block."""
        block_data = block.to_dict() if hasattr(block, "to_dict") else {"raw": str(block)}
        return self.broadcast_sync("blocks", block_data)

    def notify_new_transaction(self, tx) -> int:
        """Notify all subscribers of a new transaction."""
        tx_data = tx.to_dict() if hasattr(tx, "to_dict") else {"raw": str(tx)}
        return self.broadcast_sync("transactions", tx_data)

    def notify_telemetry(self, metrics: dict) -> int:
        """Notify telemetry subscribers."""
        return self.broadcast_sync("telemetry", metrics)

    def notify_mining(self, mining_info: dict) -> int:
        """Notify mining subscribers."""
        return self.broadcast_sync("mining", mining_info)

    def get_stats(self) -> dict:
        """Return connection statistics."""
        return {
            "total_connections": len(self.connections),
            "subscriptions": {
                topic: len(conns)
                for topic, conns in self.subscriptions.items()
            },
            "connections": [c.to_dict() for c in self.connections.values()],
        }

    def ping_all(self) -> int:
        """Mark all connections as alive."""
        now = time.time()
        for conn in self.connections.values():
            conn.last_ping = now
        return len(self.connections)


# Simple helper to send a single message (used in tests)
async def send_ws_message(writer, message: dict) -> bool:
    """Send a single WebSocket message."""
    if not writer:
        return False
    try:
        payload = json.dumps(message)
        writer.write(payload.encode())
        await writer.drain()
        return True
    except Exception:
        return False
