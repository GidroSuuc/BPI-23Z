from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.assembly import AssemblyOrder, AssemblyTask, ProductMaterial
from app.models.inventory import InventoryTransaction, TransactionTypeEnum
from app.crud.assembly import assembly_order, assembly_task, product
from app.crud.inventory import transaction, material
from app.schemas.assembly import AssemblyOrderCreate, AssemblyTaskCreate

class AssemblyService:
    @staticmethod
    def create_order_with_materials(
        db: Session, 
        order_in: AssemblyOrderCreate, 
        created_by_id: int
    ):
        """Создание заказа с резервированием материалов"""
        # 1. Создаем заказ
        order_data = order_in.dict()
        order_data['created_by_id'] = created_by_id
        db_order = assembly_order.create(db, obj_in=order_data)
        
        # 2. Получаем BOM (Bill of Materials)
        product_materials = db.query(ProductMaterial).filter(
            ProductMaterial.product_id == order_in.product_id
        ).all()
        
        # 3. Резервируем материалы
        for pm in product_materials:
            required_qty = pm.quantity_required * order_in.quantity
            
            # Проверяем доступность
            mat = material.get(db, id=pm.material_id)
            if mat.current_quantity < required_qty:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Недостаточно материала: {mat.name}. Требуется: {required_qty}, доступно: {mat.current_quantity}"
                )
            
            # Создаем транзакцию резервирования
            transaction.create(db, obj_in={
                "material_id": pm.material_id,
                "transaction_type": TransactionTypeEnum.RESERVATION,
                "quantity": required_qty,
                "order_id": db_order.id,
                "notes": f"Резерв для заказа {db_order.order_number}"
            })
        
        return db_order
    
    @staticmethod
    def start_task(db: Session, task_id: int, user_id: int):
        """Начало выполнения задачи"""
        db_task = assembly_task.get(db, id=task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        if db_task.assigned_to_id != user_id:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        if db_task.status not in ["assigned", "paused"]:
            raise HTTPException(status_code=400, detail="Невозможно начать задачу в текущем статусе")
        
        db_task.status = "in_progress"
        db_task.started_at = datetime.utcnow()
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Обновляем статус заказа, если нужно
        order = assembly_order.get(db, id=db_task.order_id)
        if order.status == "planned":
            order.status = "in_progress"
            db.add(order)
            db.commit()
        
        return db_task
    
    @staticmethod
    def complete_task(db: Session, task_id: int, user_id: int, notes: str = None):
        """Завершение задачи"""
        db_task = assembly_task.get(db, id=task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        
        if db_task.assigned_to_id != user_id:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        db_task.status = "completed"
        db_task.completed_at = datetime.utcnow()
        db_task.notes = notes
        db.add(db_task)
        db.commit()
        
        # Проверяем, все ли задачи заказа завершены
        order = assembly_order.get(db, id=db_task.order_id)
        tasks = assembly_task.get_by_order(db, order_id=order.id)
        
        all_completed = all(t.status == "completed" for t in tasks)
        if all_completed:
            order.status = "completed"
            order.actual_end = datetime.utcnow()
            db.add(order)
            
            # Списание материалов
            AssemblyService._write_off_materials(db, order.id)
        
        db.commit()
        return db_task
    
    @staticmethod
    def _write_off_materials(db: Session, order_id: int):
        """Списание материалов после завершения заказа"""
        # Находим все резервирования для этого заказа
        reservations = transaction.get_by_order(db, order_id=order_id)
        
        for res in reservations:
            # Создаем транзакцию списания
            transaction.create(db, obj_in={
                "material_id": res.material_id,
                "transaction_type": TransactionTypeEnum.OUTGOING,
                "quantity": res.quantity,
                "order_id": order_id,
                "notes": f"Списание по заказу {order_id}"
            })