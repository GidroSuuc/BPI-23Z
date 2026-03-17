from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List
from decimal import Decimal

from app.api.v1.dependencies import get_current_senior_user, get_current_admin_user
from app.core.database import get_db
from app.schemas.inventory import (
    Material, MaterialCreate, MaterialUpdate, MaterialCategory,
    InventoryTransaction, InventoryTransactionCreate, StockAlert,
    InventoryDashboard
)
from app.crud.inventory import material_category, material, transaction, stock_alert

router = APIRouter()

@router.get("/dashboard", response_model=InventoryDashboard)
def get_inventory_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_senior_user)
) -> Any:
    """
    Дашборд склада
    """
    total_materials = material.count(db)
    low_stock = len(material.get_low_stock(db))
    total_value = material.get_total_value(db)
    
    recent_transactions = transaction.get_multi(db, skip=0, limit=10)
    recent_alerts = stock_alert.get_unresolved(db, skip=0, limit=5)
    
    return InventoryDashboard(
        total_materials=total_materials,
        low_stock_count=low_stock,
        total_value=total_value,
        recent_transactions=recent_transactions,
        recent_alerts=recent_alerts
    )

@router.get("/materials/low-stock", response_model=List[Material])
def get_low_stock_materials(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_senior_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Получить материалы с низким остатком
    """
    return material.get_low_stock(db, skip=skip, limit=limit)

@router.post("/materials/{material_id}/adjust")
def adjust_material_stock(
    material_id: int,
    adjustment_type: str = Query(..., regex="^(increase|decrease)$"),
    quantity: Decimal = Query(..., gt=0),
    notes: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_senior_user)
) -> Any:
    """
    Ручная корректировка остатка материала
    """
    db_material = material.get(db, id=material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    
    # Создаем транзакцию
    trans_type = "adjustment" if adjustment_type == "increase" else "write_off"
    
    transaction.create(db, obj_in={
        "material_id": material_id,
        "transaction_type": trans_type,
        "quantity": quantity,
        "user_id": current_user.id,
        "notes": notes or f"Ручная корректировка: {adjustment_type}"
    })
    
    return {"message": "Остаток успешно скорректирован"}