from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, List

from app.api.v1.dependencies import get_current_admin_user, get_current_senior_user
from app.core.database import get_db
from app.schemas.user import User, UserCreate, UserUpdate, UserActivity
from app.crud.user import user, user_activity

router = APIRouter()

@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
    role: str = None
) -> Any:
    """
    Получить список пользователей (только для админов)
    """
    if role:
        users_list = user.get_by_role(db, role=role, skip=skip, limit=limit)
    else:
        users_list = user.get_multi(db, skip=skip, limit=limit)
    return users_list

@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
    user_in: UserCreate,
) -> Any:
    """
    Создать нового пользователя
    """
    db_user = user.get_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )
    
    db_user = user.get_by_username(db, username=user_in.username)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем уже существует"
        )
    
    return user.create(db, obj_in=user_in)

@router.get("/assemblers", response_model=List[User])
def read_assemblers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_senior_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Получить список сборщиков (для старших)
    """
    return user.get_assemblers(db, skip=skip, limit=limit)

@router.get("/{user_id}/activities", response_model=List[UserActivity])
def read_user_activities(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Получить активность пользователя
    """
    return user_activity.get_user_activities(db, user_id=user_id, skip=skip, limit=limit)