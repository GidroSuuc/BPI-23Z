from celery import Celery
from celery.schedules import crontab
import os
from app.core.config import settings

celery_app = Celery(
    "crm_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.report_tasks",
        "app.tasks.cleanup_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Конфигурация
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
)

# Расписание задач
celery_app.conf.beat_schedule = {
    'send-daily-reports': {
        'task': 'app.tasks.report_tasks.send_daily_reports',
        'schedule': crontab(hour=18, minute=0),  # 18:00 ежедневно
    },
    'check-low-stock': {
        'task': 'app.tasks.notification_tasks.check_low_stock',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
    },
    'cleanup-old-logs': {
        'task': 'app.tasks.cleanup_tasks.cleanup_old_activity_logs',
        'schedule': crontab(hour=2, minute=0),  # 2:00 ежедневно
    },
    'update-order-statistics': {
        'task': 'app.tasks.report_tasks.update_order_statistics',
        'schedule': crontab(minute=0, hour='*/1'),  # Каждый час
    },
}