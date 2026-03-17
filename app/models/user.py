from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from . import BaseModel

class RoleEnum(str, PyEnum):
    ADMIN = "admin"
    SENIOR = "senior"
    ASSEMBLER = "assembler"

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    role = Column(Enum(RoleEnum), default=RoleEnum.ASSEMBLER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    phone = Column(String(20))
    department = Column(String(100))
    
    # Связи
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    created_tasks = relationship("AssemblyTask", foreign_keys="AssemblyTask.created_by_id", back_populates="created_by")
    assigned_tasks = relationship("AssemblyTask", foreign_keys="AssemblyTask.assigned_to_id", back_populates="assigned_to")
    
    @property
    def is_admin(self):
        return self.role == RoleEnum.ADMIN
    
    @property
    def is_senior(self):
        return self.role == RoleEnum.SENIOR

class UserActivity(BaseModel):
    __tablename__ = "user_activities"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    details = Column(JSON)
    
    user = relationship("User", back_populates="activities")