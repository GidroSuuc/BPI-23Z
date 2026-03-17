from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any, List
from datetime import datetime

from app.api.v1.dependencies import (
    get_current_user, get_current_senior_user, get_current_assembler_user
)
from app.core.database import get_db
from app.schemas.assembly import (
    AssemblyOrder, AssemblyOrderCreate, AssemblyTask, AssemblyTaskCreate,
    OrderDashboard, TaskStatusEnum
)
from app.crud.assembly import assembly_order, assembly_task, product
from app.services.assembly_service import AssemblyService

router = APIRouter()

@router.get("/dashboard", response_model=OrderDashboard)
def get_assembly_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Дашборд сборки
    """
    # Статистика зависит от роли
    if current_user.is_admin or current_user.is_senior:
        total_orders = assembly_order.count(db)
        in_progress = assembly_order.count_by_status(db, "in_progress")
        completed_today = assembly_order.count_completed_today(db)
        overdue = assembly_order.count_overdue(db)
        recent_orders = assembly_order.get_multi(db, skip=0, limit=10)
    else:
        total_orders = 0
        in_progress = 0
        completed_today = 0
        overdue = 0
        recent_orders = []
    
    # Задачи текущего пользователя
    my_tasks = assembly_task.get_user_tasks(
        db, user_id=current_user.id, status=["assigned", "in_progress"]
    )
    
    return OrderDashboard(
        total_orders=total_orders,
        in_progress=in_progress,
        completed_today=completed_today,
        overdue=overdue,
        recent_orders=recent_orders,
        my_tasks=my_tasks
    )

@router.post("/orders/", response_model=AssemblyOrder)
def create_assembly_order(
    *,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_senior_user),
    order_in: AssemblyOrderCreate
) -> Any:
    """
    Создать новый заказ на сборку с резервированием материалов
    """
    return AssemblyService.create_order_with_materials(
        db, order_in=order_in, created_by_id=current_user.id
    )

@router.get("/my-tasks", response_model=List[AssemblyTask])
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_assembler_user),
    status: List[str] = Query(None)
) -> Any:
    """
    Получить мои задачи
    """
    return assembly_task.get_user_tasks(
        db, user_id=current_user.id, status=status
    )

@router.post("/tasks/{task_id}/start", response_model=AssemblyTask)
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_assembler_user)
) -> Any:
    """
    Начать выполнение задачи
    """
    return AssemblyService.start_task(db, task_id=task_id, user_id=current_user.id)

@router.post("/tasks/{task_id}/complete", response_model=AssemblyTask)
def complete_task(
    task_id: int,
    notes: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_assembler_user)
) -> Any:
    """
    Завершить задачу
    """
    return AssemblyService.complete_task(
        db, task_id=task_id, user_id=current_user.id, notes=notes
    )

@router.post("/tasks/bulk-assign")
def bulk_assign_tasks(
    task_ids: List[int],
    assigned_to_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_senior_user)
) -> Any:
    """
    Массовое назначение задач
    """
    updated = []
    for task_id in task_ids:
        db_task = assembly_task.get(db, id=task_id)
        if db_task:
            db_task.assigned_to_id = assigned_to_id
            db.add(db_task)
            updated.append(task_id)
    
    db.commit()
    return {"message": f"Назначено {len(updated)} задач", "task_ids": updated}