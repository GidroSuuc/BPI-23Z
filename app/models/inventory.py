from sqlalchemy import Column, String, Text, Numeric, Integer, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from . import BaseModel

class UnitEnum(str, PyEnum):
    PCS = "pcs"
    KG = "kg"
    M = "m"
    L = "l"
    M2 = "m2"
    ROLL = "roll"

class TransactionTypeEnum(str, PyEnum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RESERVATION = "reservation"
    WRITE_OFF = "write_off"

class MaterialCategory(BaseModel):
    __tablename__ = "material_categories"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("material_categories.id"))
    
    parent = relationship("MaterialCategory", remote_side="MaterialCategory.id")
    materials = relationship("Material", back_populates="category")

class Material(BaseModel):
    __tablename__ = "materials"
    
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("material_categories.id"))
    
    unit = Column(Enum(UnitEnum), nullable=False)
    min_quantity = Column(Numeric(10, 2), default=0)
    current_quantity = Column(Numeric(10, 2), default=0)
    
    cost_price = Column(Numeric(10, 2), default=0)
    supplier = Column(String(200))
    location = Column(String(100))
    barcode = Column(String(100), unique=True)
    
    image_url = Column(String(500))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Связи
    category = relationship("MaterialCategory", back_populates="materials")
    transactions = relationship("InventoryTransaction", back_populates="material", cascade="all, delete-orphan")
    product_materials = relationship("ProductMaterial", back_populates="material")
    
    @property
    def is_low_stock(self):
        return self.current_quantity <= self.min_quantity

class InventoryTransaction(BaseModel):
    __tablename__ = "inventory_transactions"
    
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    
    from_location = Column(String(100))
    to_location = Column(String(100))
    
    order_id = Column(Integer, ForeignKey("assembly_orders.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    document_number = Column(String(100))
    document_date = Column(String(20))
    notes = Column(Text)
    
    # Связи
    material = relationship("Material", back_populates="transactions")
    order = relationship("AssemblyOrder", back_populates="material_transactions")
    user = relationship("User")

class StockAlert(BaseModel):
    __tablename__ = "stock_alerts"
    
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # low_stock, expired, missing
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_by_id = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    
    material = relationship("Material")
    resolved_by = relationship("User")