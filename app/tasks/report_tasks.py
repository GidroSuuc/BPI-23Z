from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.crud.assembly import assembly_order
from app.crud.inventory import material
from app.services.email_service import EmailService
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def generate_daily_report(date_str=None):
    """Генерация ежедневного отчета"""
    db = SessionLocal()
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow().date()
        
        # Собираем статистику
        orders_today = assembly_order.get_by_date(db, date)
        completed_orders = [o for o in orders_today if o.status == "completed"]
        
        # Создаем Excel отчет
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Лист с заказами
            orders_data = []
            for order in orders_today:
                orders_data.append({
                    "Номер заказа": order.order_number,
                    "Изделие": order.product.name,
                    "Количество": order.quantity,
                    "Статус": order.status,
                    "Прогресс": f"{order.progress}%",
                    "Клиент": order.client_name,
                    "Ответственный": order.supervisor.full_name if order.supervisor else ""
                })
            
            if orders_data:
                df_orders = pd.DataFrame(orders_data)
                df_orders.to_excel(writer, sheet_name="Заказы", index=False)
            
            # Лист со статистикой
            stats_data = {
                "Метрика": ["Всего заказов", "Завершено", "В работе", "Приостановлено"],
                "Значение": [
                    len(orders_today),
                    len(completed_orders),
                    len([o for o in orders_today if o.status == "in_progress"]),
                    len([o for o in orders_today if o.status == "paused"])
                ]
            }
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name="Статистика", index=False)
        
        output.seek(0)
        
        # Отправляем email
        email_service = EmailService()
        recipients = ["senior@company.com", "admin@company.com"]
        
        email_service.send_email_with_attachment(
            recipients=recipients,
            subject=f"Ежедневный отчет за {date.strftime('%d.%m.%Y')}",
            template_name="daily_report.html",
            context={
                "date": date.strftime("%d.%m.%Y"),
                "total_orders": len(orders_today),
                "completed_orders": len(completed_orders),
            },
            attachments=[
                {
                    "filename": f"report_{date.strftime('%Y%m%d')}.xlsx",
                    "content": output.read(),
                    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }
            ]
        )
        
        return {"generated": True, "date": date.isoformat()}
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise
    finally:
        db.close()

@celery_app.task
def update_order_statistics():
    """Обновление статистики заказов"""
    db = SessionLocal()
    try:
        # Считаем среднее время выполнения
        from app.crud.assembly import assembly_task
        from sqlalchemy import func
        
        # Пример агрегации
        result = db.query(
            func.avg(AssemblyTask.actual_hours)
        ).filter(
            AssemblyTask.status == "completed",
            AssemblyTask.completed_at >= datetime.utcnow() - timedelta(days=30)
        ).scalar()
        
        # Сохраняем в кэш или базу
        from app.core.redis import redis_client
        redis_client.setex(
            "order_statistics:avg_completion_time",
            3600,  # 1 час
            str(result or 0)
        )
        
        return {"avg_completion_time": result}
    finally:
        db.close()
        