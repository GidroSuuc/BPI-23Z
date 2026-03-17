from pydantic import BaseModel, validator
from typing import Optional, List
from decimal import Decimal
from enum import Enum
from . import BaseSchema

class UnitEnum(str, Enum):
    PCS = "pcs"
    KG = "kg"
    M = "m"
    L = "l"
    M2 = "m2"
    ROLL = "roll"

class TransactionTypeEnum(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    RESERVATION = "reservation"
    WRITE_OFF = "write_off"

class MaterialCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class MaterialCategory(MaterialCategoryCreate, BaseSchema):
    pass

class MaterialCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    unit: UnitEnum
    min_quantity: Decimal = 0
    cost_price: Decimal = 0
    supplier: Optional[str] = None
    location: Optional[str] = None
    barcode: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('min_quantity', 'cost_price')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError('Значение не может быть отрицательным')
        return v

class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    min_quantity: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class Material(MaterialCreate, BaseSchema):
    current_quantity: Decimal
    is_active: bool
    is_low_stock: bool = False
    image_url: Optional[str] = None

class MaterialWithTransactions(Material):
    transactions: List["InventoryTransaction"] = []

class InventoryTransactionCreate(BaseModel):
    material_id: int
    transaction_type: TransactionTypeEnum
    quantity: Decimal
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    order_id: Optional[int] = None
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Количество должно быть больше 0')
        return v

class InventoryTransaction(InventoryTransactionCreate, BaseSchema):
    user_id: Optional[int] = None

class StockAlertCreate(BaseModel):
    material_id: int
    alert_type: str
    message: str

class StockAlert(StockAlertCreate, BaseSchema):
    is_resolved: bool = False
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[str] = None

class InventoryDashboard(BaseModel):
    total_materials: int
    low_stock_count: int
    total_value: Decimal
    recent_transactions: List[InventoryTransaction]
    recent_alerts: List[StockAlert]