from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, UserActivity
from app.schemas.user import UserCreate, UserUpdate, UserActivityCreate
from app.core.security import get_password_hash, verify_password
from .base import CRUDBase

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=obj_in.role,
            phone=obj_in.phone,
            department=obj_in.department,
            is_active=True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def authenticate(self, db: Session, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        search = f"%{query}%"
        return db.query(User).filter(
            or_(
                User.email.ilike(search),
                User.username.ilike(search),
                User.full_name.ilike(search)
            )
        ).offset(skip).limit(limit).all()
    
    def get_assemblers(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        from app.models.user import RoleEnum
        return db.query(User).filter(User.role == RoleEnum.ASSEMBLER).offset(skip).limit(limit).all()

class CRUDUserActivity(CRUDBase[UserActivity, UserActivityCreate, UserActivityCreate]):
    def create_activity(self, db: Session, *, user_id: int, action: str, 
                       ip_address: str = None, user_agent: str = None, 
                       details: dict = None) -> UserActivity:
        db_obj = UserActivity(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {}
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_user_activities(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        return db.query(UserActivity).filter(
            UserActivity.user_id == user_id
        ).order_by(UserActivity.created_at.desc()).offset(skip).limit(limit).all()

user = CRUDUser(User)
user_activity = CRUDUserActivity(UserActivity)