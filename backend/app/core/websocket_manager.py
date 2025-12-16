import asyncio
import uuid
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Gestiona conexiones WebSocket por usuario en un solo worker."""

    def __init__(self) -> None:
        self.active_connections: dict[uuid.UUID, WebSocket] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: uuid.UUID) -> None:
        websocket = self.active_connections.pop(user_id, None)
        if websocket:
            try:
                asyncio.create_task(websocket.close())
            except Exception:
                # Si ya está cerrado, ignorar
                pass

    async def send_to_user(self, user_id: uuid.UUID, message: Any) -> None:
        websocket = self.active_connections.get(user_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception:
                # Si falla el envío, eliminamos la conexión inválida
                self.disconnect(user_id)

    async def send_to_users(self, user_ids: list[uuid.UUID], message: Any) -> None:
        for uid in user_ids:
            await self.send_to_user(uid, message)

    def is_connected(self, user_id: uuid.UUID) -> bool:
        return user_id in self.active_connections


# Singleton compartido
manager = ConnectionManager()
