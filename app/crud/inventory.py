from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from decimal import Decimal
from app.models.inventory import Material, MaterialCategory, InventoryTransaction, StockAlert
from app.schemas.inventory import (
    MaterialCreate, MaterialUpdate, MaterialCategoryCreate,
    InventoryTransactionCreate, StockAlertCreate
)
from .base import CRUDBase

class CRUDMaterialCategory(CRUDBase[MaterialCategory, MaterialCategoryCreate, MaterialCategoryCreate]):
    def get_by_name(self, db: Session, name: str) -> Optional[MaterialCategory]:
        return db.query(MaterialCategory).filter(MaterialCategory.name == name).first()
    
    def get_tree(self, db: Session) -> List[MaterialCategory]:
        # Получение дерева категорий
        categories = db.query(MaterialCategory).all()
        return self._build_tree(categories)
    
    def _build_tree(self, categories, parent_id=None):
        tree = []
        for category in categories:
            if category.parent_id == parent_id:
                children = self._build_tree(categories, category.id)
                category_dict = {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'children': children
                }
                tree.append(category_dict)
        return tree

class CRUDMaterial(CRUDBase[Material, MaterialCreate, MaterialUpdate]):
    def get_by_sku(self, db: Session, sku: str) -> Optional[Material]:
        return db.query(Material).filter(Material.sku == sku).first()
    
    def get_by_barcode(self, db: Session, barcode: str) -> Optional[Material]:
        return db.query(Material).filter(Material.barcode == barcode).first()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Material]:
        search = f"%{query}%"
        return db.query(Material).filter(
            or_(
                Material.sku.ilike(search),
                Material.name.ilike(search),
                Material.description.ilike(search),
                Material.barcode.ilike(search)
            )
        ).offset(skip).limit(limit).all()
    
    def get_low_stock(self, db: Session, skip: int = 0, limit: int = 100) -> List[Material]:
        return db.query(Material).filter(
            Material.current_quantity <= Material.min_quantity,
            Material.is_active == True
        ).offset(skip).limit(limit).all()
    
    def update_quantity(self, db: Session, *, material_id: int, delta: Decimal) -> Material:
        material = self.get(db, id=material_id)
        if material:
            material.current_quantity += delta
            db.add(material)
            db.commit()
            db.refresh(material)
        return material
    
    def get_total_value(self, db: Session) -> Decimal:
        result = db.query(
            func.sum(Material.current_quantity * Material.cost_price)
        ).scalar()
        return result or Decimal('0')

class CRUDInventoryTransaction(CRUDBase[InventoryTransaction, InventoryTransactionCreate, InventoryTransactionCreate]):
    def get_by_material(self, db: Session, material_id: int, skip: int = 0, limit: int = 100):
        return db.query(InventoryTransaction).filter(
            InventoryTransaction.material_id == material_id
        ).order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_order(self, db: Session, order_id: int):
        return db.query(InventoryTransaction).filter(
            InventoryTransaction.order_id == order_id
        ).all()

class CRUDStockAlert(CRUDBase[StockAlert, StockAlertCreate, StockAlertCreate]):
    def get_unresolved(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(StockAlert).filter(
            StockAlert.is_resolved == False
        ).offset(skip).limit(limit).all()

material_category = CRUDMaterialCategory(MaterialCategory)
material = CRUDMaterial(Material)
transaction = CRUDInventoryTransaction(InventoryTransaction)
stock_alert = CRUDStockAlert(StockAlert)