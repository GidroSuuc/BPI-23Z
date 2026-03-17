from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.crud.user import user
from app.schemas.user import Token, User

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        db_user = user.authenticate(db, email=email, password=password)
        if not db_user:
            return None
        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь неактивен"
            )
        return db_user
    
    @staticmethod
    def create_tokens(user_data: User) -> Token:
        access_token = create_access_token(data={"sub": user_data.username})
        refresh_token = create_refresh_token(data={"sub": user_data.username})
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    @staticmethod
    def refresh_token(refresh_token: str) -> Token:
        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный refresh token"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный refresh token"
            )
        
        # Здесь можно проверить, не отозван ли токен
        new_access_token = create_access_token(data={"sub": username})
        return Token(access_token=new_access_token, refresh_token=refresh_token)