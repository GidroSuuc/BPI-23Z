from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from enum import Enum
from . import BaseSchema

class RoleEnum(str, Enum):
    ADMIN = "admin"
    SENIOR = "senior"
    ASSEMBLER = "assembler"

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: RoleEnum = RoleEnum.ASSEMBLER
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен быть не менее 8 символов')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[RoleEnum] = None

class UserInDB(UserBase, BaseSchema):
    role: RoleEnum
    is_active: bool
    is_superuser: bool = False

class User(UserInDB):
    pass

class UserWithToken(User):
    token: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserActivityCreate(BaseModel):
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[dict] = None

class UserActivity(BaseSchema):
    user_id: int
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Optional[dict]