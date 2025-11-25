"""
Модели пользователей
"""
from typing import Optional
from pydantic import Field, validator
from .base import BaseModel, IDMixin, TimestampMixin

# Используем str вместо EmailStr для простоты
EmailStr = str


class UserBase(BaseModel):
    """Базовая модель пользователя"""
    login: str = Field(..., min_length=3, max_length=50, description="Логин пользователя")
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    full_name: str = Field("", max_length=100, description="Полное имя пользователя")
    email: EmailStr = Field(..., description="Email адрес")
    phone: str = Field("", max_length=20, description="Номер телефона")
    role: str = Field("manager", description="Роль пользователя")
    is_admin: bool = Field(False, description="Является ли администратором")
    is_active: bool = Field(True, description="Активен ли пользователь")


class UserCreate(UserBase):
    """Модель для создания пользователя"""
    password: str = Field(..., min_length=6, description="Пароль")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v


class UserUpdate(BaseModel):
    """Модель для обновления пользователя"""
    login: Optional[str] = Field(None, min_length=3, max_length=50)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    """Модель для входа пользователя"""
    login: Optional[str] = Field(None, description="Логин пользователя")
    username: Optional[str] = Field(None, description="Имя пользователя")
    password: str = Field(..., description="Пароль")
    
    @validator('login', 'username')
    def validate_login_or_username(cls, v, values):
        # Если оба поля пустые, это ошибка
        if not v and not values.get('username' if 'login' in values else 'login'):
            raise ValueError('Необходимо указать login или username')
        return v
    
    def get_login_value(self) -> str:
        """Возвращает значение для логина (приоритет login, затем username)"""
        return self.login or self.username


class PasswordChange(BaseModel):
    """Модель для изменения пароля"""
    new_password: str = Field(..., min_length=6, description="Новый пароль")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """Модель ответа с данными пользователя"""
    pass


class User(UserBase, IDMixin, TimestampMixin):
    """Полная модель пользователя (для внутреннего использования)"""
    password_hash: str = Field(..., description="Хеш пароля")
