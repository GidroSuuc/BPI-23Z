from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    Зависимость для получения сессии БД
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание таблиц (для разработки)
def create_tables():
    from app.models.user import Base
    Base.metadata.create_all(bind=engine)