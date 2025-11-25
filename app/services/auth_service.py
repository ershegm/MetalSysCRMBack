"""
Сервис аутентификации
"""
from typing import Optional, Dict, Any
from datetime import timedelta

from ..core.security import security_manager
from ..core.database import db_manager
from ..core.exceptions import AuthenticationError, AuthorizationError
from ..models.user import UserLogin, UserCreate, UserUpdate, PasswordChange


class AuthService:
    """Сервис аутентификации и авторизации"""
    
    def __init__(self):
        self.security_manager = security_manager
        self.db_manager = db_manager
    
    async def authenticate_user(self, user_credentials: UserLogin) -> Dict[str, str]:
        """Аутентификация пользователя"""
        user = self.security_manager.authenticate_user(
            user_credentials.get_login_value(), 
            user_credentials.password
        )
        
        if not user:
            raise AuthenticationError("Неверный логин или пароль")
        
        access_token = self.security_manager.create_user_token(user)
        return {
            "access_token": access_token, 
            "token_type": "bearer"
        }
    
    async def get_current_user_info(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Получение информации о текущем пользователе"""
        return {
            "id": current_user['id'],
            "username": current_user['username'],
            "email": current_user['email'],
            "is_admin": bool(current_user['is_admin']),
            "is_active": bool(current_user['is_active']),
            "created_at": current_user['created_at']
        }
    
    async def verify_admin_access(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Проверка прав администратора"""
        if not current_user.get('is_admin'):
            raise AuthorizationError("Недостаточно прав для выполнения операции")
        return current_user

