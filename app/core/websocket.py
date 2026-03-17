from typing import Dict, List, Set
import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # user_id -> список соединений
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Группы для рассылки (например, по цеху)
        self.room_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass
    
    async def send_to_role(self, message: dict, role: str):
        """Отправка сообщения всем пользователям с определенной ролью"""
        # Здесь нужно получить всех пользователей с этой ролью из БД
        # Упрощенный пример
        pass
    
    async def broadcast(self, message: dict):
        """Широковещательная рассылка"""
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()