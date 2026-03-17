from pydantic_settings import BaseSettings
from typing import Optional
import secrets

class Settings(BaseSettings):
    # Базовые настройки
    PROJECT_NAME: str = "CRM System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Безопасность
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # База данных
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost/crm_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis (для кэша и Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]
    
    # Настройки приложения
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()