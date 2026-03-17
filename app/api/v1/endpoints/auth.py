from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db
from app.schemas.user import Token, User
from app.services.auth_service import AuthService
from app.crud.user import user_activity

router = APIRouter()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 совместимый логин, получаем токены
    """
    db_user = AuthService.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    
    tokens = AuthService.create_tokens(db_user)
    
    # Логируем вход
    user_activity.create_activity(
        db,
        user_id=db_user.id,
        action="login",
        details={"method": "password"}
    )
    
    return tokens

@router.post("/refresh", response_model=Token)
def refresh_token(token: str) -> Any:
    """
    Обновление access токена
    """
    return AuthService.refresh_token(token)

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Выход из системы
    """
    user_activity.create_activity(
        db,
        user_id=current_user.id,
        action="logout"
    )
    return {"message": "Успешный выход"}

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    Получить информацию о текущем пользователе
    """
    return current_user