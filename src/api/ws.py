"""
WebSocket endpoint and connection manager.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send a JSON message to all connected clients."""
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


# Singleton manager
manager = ConnectionManager()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint that pushes real-time updates to clients."""
    await manager.connect(websocket)

    # Send initial state
    app_state = websocket.app.state.app
    scores = {}
    for ticker, ts in app_state.tickers.items():
        if ts.is_monitoring:
            scores[ticker] = {
                "score": ts.current_score,
                "recommendation": ts.recommendation,
                "pipeline_step": ts.pipeline_step,
                "timestamp": datetime.now().isoformat(),
            }

    await websocket.send_json({
        "type": "initial_state",
        "data": {
            "monitored_tickers": [
                t for t, s in app_state.tickers.items() if s.is_monitoring
            ],
            "data_source": app_state.data_source,
            "models_loaded": app_state.models_loaded,
            "scores": scores,
        },
    })

    try:
        # Keep connection alive, listen for pings
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
