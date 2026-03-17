from typing import List
from app.core.websocket import manager
from app.crud.user import user as user_crud
from sqlalchemy.orm import Session
from datetime import datetime

class NotificationService:
    @staticmethod
    async def send_task_assignment(db: Session, task_id: int, assigned_to_id: int, assigned_by_id: int):
        """Уведомление о назначении задачи"""
        assigned_to = user_crud.get(db, id=assigned_to_id)
        assigned_by = user_crud.get(db, id=assigned_by_id)
        
        if assigned_to:
            await manager.send_personal_message({
                "type": "task_assigned",
                "task_id": task_id,
                "assigned_by": assigned_by.full_name if assigned_by else "Система",
                "assigned_at": datetime.utcnow().isoformat(),
                "priority": "medium",
                "message": f"Вам назначена новая задача #{task_id}"
            }, assigned_to_id)
    
    @staticmethod
    async def send_low_stock_alert(db: Session, material_id: int, current_qty: float, min_qty: float):
        """Уведомление о низком остатке"""
        # Получаем всех старших и админов
        seniors_and_admins = user_crud.get_by_roles(db, roles=["senior", "admin"])
        
        for user in seniors_and_admins:
            await manager.send_personal_message({
                "type": "low_stock",
                "material_id": material_id,
                "current_quantity": current_qty,
                "min_quantity": min_qty,
                "message": f"Низкий остаток материала #{material_id}",
                "timestamp": datetime.utcnow().isoformat()
            }, user.id)
    
    @staticmethod
    async def send_order_status_change(db: Session, order_id: int, old_status: str, new_status: str, changed_by_id: int):
        """Уведомление об изменении статуса заказа"""
        changed_by = user_crud.get(db, id=changed_by_id)
        
        await manager.broadcast({
            "type": "order_status_changed",
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by.full_name if changed_by else "Система",
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Статус заказа #{order_id} изменен: {old_status} → {new_status}"
        })
    
    @staticmethod
    async def send_daily_summary(db: Session, date: datetime.date):
        """Ежедневный отчет для старших"""
        # Получаем статистику за день
        from app.crud.assembly import assembly_order
        stats = assembly_order.get_daily_stats(db, date)
        
        seniors = user_crud.get_by_roles(db, roles=["senior", "admin"])
        
        for user in seniors:
            await manager.send_personal_message({
                "type": "daily_summary",
                "date": date.isoformat(),
                "stats": stats,
                "message": f"Ежедневный отчет за {date.strftime('%d.%m.%Y')}",
                "timestamp": datetime.utcnow().isoformat()
            }, user.id)