from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Optional
import json
from datetime import datetime

from app.core.websocket import manager
from app.api.v1.dependencies import get_current_user_ws
from app.crud.user import user as user_crud

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """Основное WebSocket соединение"""
    if not token:
        await websocket.close(code=1008)
        return
    
    try:
        # Аутентификация по токену
        user = await get_current_user_ws(token)
        if not user:
            await websocket.close(code=1008)
            return
        
        await manager.connect(websocket, user.id)
        
        # Отправляем приветственное сообщение
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user.id,
            "message": "WebSocket соединение установлено",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            while True:
                data = await websocket.receive_text()
                
                # Обработка входящих сообщений
                try:
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    
                    elif message.get("type") == "subscribe":
                        # Подписка на определенные события
                        events = message.get("events", [])
                        # Логика подписки
                        pass
                    
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Неверный формат JSON"
                    })
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id)
            
    except Exception as e:
        await websocket.close(code=1011)