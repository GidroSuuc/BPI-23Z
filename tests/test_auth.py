import pytest
from fastapi import status

def test_login_success(client, db, assembler_user):
    # Подготовка: нужно установить пароль
    from app.core.security import get_password_hash
    assembler_user.hashed_password = get_password_hash("testpassword")
    db.commit()
    
    response = client.post("/api/v1/auth/login", data={
        "username": assembler_user.email,
        "password": "testpassword"
    })
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, assembler_user):
    response = client.post("/api/v1/auth/login", data={
        "username": assembler_user.email,
        "password": "wrongpassword"
    })
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Неверный email или пароль"

def test_get_current_user(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"

def test_protected_endpoint_no_token(client):
    response = client.get("/api/v1/users/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_refresh_token(client, assembler_user):
    # Сначала логинимся
    login_response = client.post("/api/v1/auth/login", data={
        "username": assembler_user.email,
        "password": "testpassword"
    })
    refresh_token = login_response.json()["refresh_token"]
    
    # Обновляем токен
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()