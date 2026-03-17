from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum
from . import BaseSchema

class OrderStatusEnum(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatusEnum(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    ON_REVIEW = "on_review"
    COMPLETED = "completed"
    REJECTED = "rejected"

class ProductCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    default_time: int = 60
    is_active: bool = True

class Product(ProductCreate, BaseSchema):
    image_url: Optional[str] = None

class ProductMaterialCreate(BaseModel):
    product_id: int
    material_id: int
    quantity_required: Decimal
    notes: Optional[str] = None

class ProductMaterial(ProductMaterialCreate, BaseSchema):
    material_name: Optional[str] = None

class AssemblyStageCreate(BaseModel):
    product_id: int
    name: str
    description: Optional[str] = None
    order: int
    estimated_time: int = 30
    is_quality_checkpoint: bool = False

class AssemblyStage(AssemblyStageCreate, BaseSchema):
    pass

class AssemblyOrderCreate(BaseModel):
    product_id: int
    quantity: int = 1
    priority: PriorityEnum = PriorityEnum.MEDIUM
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    supervisor_id: Optional[int] = None
    client_name: Optional[str] = None
    client_order: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Количество должно быть не менее 1')
        return v

class AssemblyOrderUpdate(BaseModel):
    status: Optional[OrderStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    supervisor_id: Optional[int] = None
    notes: Optional[str] = None

class AssemblyOrder(AssemblyOrderCreate, BaseSchema):
    order_number: str
    status: OrderStatusEnum = OrderStatusEnum.DRAFT
    created_by_id: int
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    progress: int = 0

class AssemblyTaskCreate(BaseModel):
    order_id: int
    stage_id: int
    assigned_to_id: int
    estimated_hours: Optional[Decimal] = None
    notes: Optional[str] = None

class AssemblyTaskUpdate(BaseModel):
    status: Optional[TaskStatusEnum] = None
    actual_hours: Optional[Decimal] = None
    notes: Optional[str] = None
    quality_check: Optional[bool] = None
    check_notes: Optional[str] = None
    attachments: Optional[List[str]] = None

class AssemblyTask(AssemblyTaskCreate, BaseSchema):
    created_by_id: int
    status: TaskStatusEnum = TaskStatusEnum.ASSIGNED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    actual_hours: Optional[Decimal] = None
    quality_check: Optional[bool] = None
    check_notes: Optional[str] = None
    attachments: Optional[List[str]] = None
    
    # Дополнительные поля для фронтенда
    stage_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    product_name: Optional[str] = None
    order_number: Optional[str] = None

class TaskAssignment(BaseModel):
    task_ids: List[int]
    assigned_to_id: int

class OrderDashboard(BaseModel):
    total_orders: int
    in_progress: int
    completed_today: int
    overdue: int
    recent_orders: List[AssemblyOrder]
    my_tasks: List[AssemblyTask]