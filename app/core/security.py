"""
Система безопасности и аутентификации
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings
from .database import db_manager
from .exceptions import AuthenticationError, AuthorizationError

# Настройка HTTPBearer
security = HTTPBearer()


class SecurityManager:
    """Менеджер безопасности"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.token_expire_minutes = settings.access_token_expire_minutes
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создает JWT токен"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Проверяет JWT токен"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            login: str = payload.get("sub")
            if login is None:
                return None
            return login
        except jwt.PyJWTError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Хеширует пароль"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет пароль"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def authenticate_user(self, login: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентифицирует пользователя"""
        user = db_manager.get_user_by_login(login)
        if not user:
            return None
        
        if not self.verify_password(password, user['password_hash']):
            return None
        
        return user
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Получает текущего пользователя из токена"""
        login = self.verify_token(credentials.credentials)
        if login is None:
            raise AuthenticationError("Недействительный токен")
        
        user = db_manager.get_user_by_login(login)
        if user is None:
            raise AuthenticationError("Пользователь не найден или деактивирован")
        
        return user
    
    def get_current_admin_user(self, current_user: Dict[str, Any] = Depends(None)) -> Dict[str, Any]:
        """Проверяет, что пользователь является администратором"""
        if current_user is None:
            current_user = self.get_current_user()
        
        if not current_user.get('is_admin'):
            raise AuthorizationError("Недостаточно прав для выполнения операции")
        
        return current_user
    
    def create_user_token(self, user: Dict[str, Any]) -> str:
        """Создает токен для пользователя"""
        access_token_expires = timedelta(minutes=self.token_expire_minutes)
        access_token = self.create_access_token(
            data={"sub": user['login']}, expires_delta=access_token_expires
        )
        return access_token


# Глобальный экземпляр
security_manager = SecurityManager()

# Dependency функции для FastAPI
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency для получения текущего пользователя"""
    return security_manager.get_current_user(credentials)


def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency для получения текущего администратора"""
    return security_manager.get_current_admin_user(current_user)

