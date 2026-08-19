
from fastapi import WebSocket
import json


class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
    ) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        self.active_connections.pop(client_id, None)

    async def send_message(
        self,
        client_id: str,
        message: str,
    ) -> None:
        websocket = self.active_connections.get(client_id)

        if websocket is None:
            return

        await websocket.send_json({
            "type": "message",
            "text": message,
        })



