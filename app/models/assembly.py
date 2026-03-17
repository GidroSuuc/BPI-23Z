from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, Boolean, Numeric, DateTime
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime
from . import BaseModel

class OrderStatusEnum(str, PyEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PriorityEnum(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatusEnum(str, PyEnum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    ON_REVIEW = "on_review"
    COMPLETED = "completed"
    REJECTED = "rejected"

class Product(BaseModel):
    __tablename__ = "products"
    
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    default_time = Column(Integer, default=60)  # минуты
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    
    # Связи
    materials = relationship("ProductMaterial", back_populates="product", cascade="all, delete-orphan")
    stages = relationship("AssemblyStage", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("AssemblyOrder", back_populates="product")

class ProductMaterial(BaseModel):
    __tablename__ = "product_materials"
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity_required = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    
    # Связи
    product = relationship("Product", back_populates="materials")
    material = relationship("Material", back_populates="product_materials")

class AssemblyStage(BaseModel):
    __tablename__ = "assembly_stages"
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, nullable=False)
    estimated_time = Column(Integer, default=30)  # минуты
    is_quality_checkpoint = Column(Boolean, default=False)
    
    # Связи
    product = relationship("Product", back_populates="stages")
    tasks = relationship("AssemblyTask", back_populates="stage")
    
    __table_args__ = (
        UniqueConstraint('product_id', 'order', name='uq_product_stage_order'),
    )

class AssemblyOrder(BaseModel):
    __tablename__ = "assembly_orders"
    
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.DRAFT, nullable=False)
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM, nullable=False)
    
    # Даты
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Ответственные
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    
    # Клиент
    client_name = Column(String(200))
    client_order = Column(String(100))
    notes = Column(Text)
    
    # Связи
    product = relationship("Product", back_populates="orders")
    created_by = relationship("User", foreign_keys=[created_by_id])
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    tasks = relationship("AssemblyTask", back_populates="order", cascade="all, delete-orphan")
    material_transactions = relationship("InventoryTransaction", back_populates="order")
    
    @property
    def progress(self):
        total = len(self.tasks)
        if total == 0:
            return 0
        completed = len([t for t in self.tasks if t.status == TaskStatusEnum.COMPLETED])
        return int((completed / total) * 100)

class AssemblyTask(BaseModel):
    __tablename__ = "assembly_tasks"
    
    order_id = Column(Integer, ForeignKey("assembly_orders.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("assembly_stages.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.ASSIGNED, nullable=False)
    
    # Время работы
    estimated_hours = Column(Numeric(5, 2))
    actual_hours = Column(Numeric(5, 2))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Детали выполнения
    notes = Column(Text)
    quality_check = Column(Boolean)
    check_notes = Column(Text)
    attachments = Column(JSON)  # Список ссылок на файлы
    
    # Связи
    order = relationship("AssemblyOrder", back_populates="tasks")
    stage = relationship("AssemblyStage", back_populates="tasks")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tasks")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")