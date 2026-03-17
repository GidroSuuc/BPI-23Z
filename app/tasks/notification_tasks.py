from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.services.notification_service import NotificationService
from app.crud.inventory import material
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def check_low_stock(self):
    """Проверка низкого остатка материалов"""
    db = SessionLocal()
    try:
        low_stock_materials = material.get_low_stock(db)
        
        for mat in low_stock_materials:
            # Отправляем уведомление
            NotificationService.send_low_stock_alert(
                db,
                material_id=mat.id,
                current_qty=float(mat.current_quantity),
                min_qty=float(mat.min_quantity)
            )
            
            logger.info(f"Low stock alert sent for material {mat.sku}")
        
        return {"checked": len(low_stock_materials), "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Error in check_low_stock: {e}")
        self.retry(countdown=60, exc=e)
    finally:
        db.close()

@celery_app.task
def send_bulk_notifications(user_ids, message_type, data):
    """Массовая рассылка уведомлений"""
    db = SessionLocal()
    try:
        for user_id in user_ids:
            # Отправляем уведомление каждому пользователю
            NotificationService.send_personal_notification(
                db,
                user_id=user_id,
                message_type=message_type,
                data=data
            )
        
        return {"sent_to": len(user_ids)}
    finally:
        db.close()