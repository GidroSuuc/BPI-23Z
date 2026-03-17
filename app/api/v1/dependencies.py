from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.crud.user import user
from app.schemas.user import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    db_user = user.get_by_username(db, username=token_data.username)
    if db_user is None:
        raise credentials_exception
    if not db_user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")
    
    return db_user

def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")
    return current_user

def get_current_admin_user(current_user = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user

def get_current_senior_user(current_user = Depends(get_current_user)):
    if not (current_user.is_admin or current_user.is_senior):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user

def get_current_assembler_user(current_user = Depends(get_current_user)):
    if current_user.is_assembler:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Только для сборщиков"
    )