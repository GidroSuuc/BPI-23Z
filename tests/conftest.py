import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import get_db, Base
from app.main import app
from app.core.security import create_access_token
from app.models.user import User, RoleEnum

# Тестовая база данных (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db():
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # Мокаем зависимость базы данных
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def admin_user(db):
    user = User(
        email="admin@test.com",
        username="admin",
        hashed_password="hashed_password",
        role=RoleEnum.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_token(admin_user):
    return create_access_token(data={"sub": admin_user.username})

@pytest.fixture(scope="function")
def senior_user(db):
    user = User(
        email="senior@test.com",
        username="senior",
        hashed_password="hashed_password",
        role=RoleEnum.SENIOR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def assembler_user(db):
    user = User(
        email="assembler@test.com",
        username="assembler",
        hashed_password="hashed_password",
        role=RoleEnum.ASSEMBLER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user