"""
API роуты для пользователей
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..deps import get_user_service
from ...core.security import get_current_admin_user, get_current_user
from ...models.user import UserCreate, UserUpdate, UserResponse, PasswordChange
from ...services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    current_user: dict = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Получение всех пользователей (для аутентифицированных пользователей)"""
    return await user_service.get_all_users()


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Создание пользователя (только для админов)"""
    return await user_service.create_user(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Обновление пользователя (только для админов)"""
    return await user_service.update_user(user_id, user_update)


@router.put("/{user_id}/toggle-admin")
async def toggle_admin_status(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Переключение статуса администратора"""
    return await user_service.toggle_admin_status(user_id)


@router.put("/{user_id}/toggle-active")
async def toggle_user_active_status(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Переключение статуса активности пользователя"""
    return await user_service.toggle_user_active_status(user_id)


@router.put("/{user_id}/change-password")
async def change_user_password(
    user_id: int,
    password_change: PasswordChange,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Изменение пароля пользователя"""
    return await user_service.change_user_password(user_id, password_change)


@router.put("/{user_id}/regenerate-password")
async def regenerate_user_password(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Перегенерация пароля пользователя"""
    return await user_service.regenerate_password(user_id)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: dict = Depends(get_current_admin_user),
    user_service: UserService = Depends(get_user_service)
):
    """Удаление пользователя"""
    return await user_service.delete_user(user_id)
