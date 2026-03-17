from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, inventory, assembly

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Аутентификация"])
api_router.include_router(users.router, prefix="/users", tags=["Пользователи"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Склад"])
api_router.include_router(assembly.router, prefix="/assembly", tags=["Сборка"])