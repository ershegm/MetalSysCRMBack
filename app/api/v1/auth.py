"""
API роуты для аутентификации
"""
from fastapi import APIRouter, Depends, HTTPException, status
from ..deps import get_auth_service
from ...core.security import get_current_user
from ...models.user import UserLogin, UserResponse
from ...services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=dict)
async def login(
    user_credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Вход пользователя"""
    return await auth_service.authenticate_user(user_credentials)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Получение информации о текущем пользователе"""
    return await auth_service.get_current_user_info(current_user)
