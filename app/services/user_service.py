"""
Сервис пользователей
"""
from typing import List, Dict, Any, Optional
from ..core.database import db_manager
from ..core.exceptions import NotFoundError, ConflictError, ValidationError
from ..models.user import UserCreate, UserUpdate, PasswordChange


class UserService:
    """Сервис управления пользователями"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получение всех пользователей"""
        return self.db_manager.get_all_users()
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        user = self.db_manager.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"Пользователь с ID {user_id} не найден")
        return user
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Создание нового пользователя"""
        # Проверяем, существует ли пользователь с таким логином или email
        existing_user = self.db_manager.get_user_by_login(user_data.login)
        if existing_user:
            raise ConflictError("Пользователь с таким логином уже существует")
        
        user_id = self.db_manager.create_user(
            user_data.login,
            user_data.username,
            user_data.email,
            user_data.password,
            user_data.full_name,
            user_data.phone,
            user_data.role,
            user_data.is_admin
        )
        
        created_user = self.db_manager.get_user_by_id(user_id)
        return {
            "id": created_user['id'],
            "login": created_user['login'],
            "username": created_user['username'],
            "full_name": created_user['full_name'],
            "email": created_user['email'],
            "phone": created_user['phone'],
            "role": created_user['role'],
            "is_admin": bool(created_user['is_admin']),
            "is_active": bool(created_user['is_active']),
            "created_at": created_user['created_at'],
            "updated_at": created_user.get('updated_at')
        }
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Dict[str, Any]:
        """Обновление пользователя"""
        # Проверяем, что пользователь существует
        user = await self.get_user_by_id(user_id)
        
        # Проверяем, что новый login не занят другим пользователем
        if user_data.login:
            existing_user = self.db_manager.get_user_by_login(user_data.login)
            if existing_user and existing_user['id'] != user_id:
                raise ConflictError("Пользователь с таким логином уже существует")
        
        updated_user = self.db_manager.update_user(
            user_id,
            user_data.login,
            user_data.username,
            user_data.full_name,
            user_data.email,
            user_data.phone,
            user_data.role,
            user_data.is_admin,
            user_data.is_active
        )
        
        return {
            "id": updated_user['id'],
            "login": updated_user['login'],
            "username": updated_user['username'],
            "full_name": updated_user['full_name'],
            "email": updated_user['email'],
            "phone": updated_user['phone'],
            "role": updated_user['role'],
            "is_admin": bool(updated_user['is_admin']),
            "is_active": bool(updated_user['is_active']),
            "created_at": updated_user['created_at'],
            "updated_at": updated_user.get('updated_at')
        }
    
    async def change_user_password(self, user_id: int, password_data: PasswordChange) -> Dict[str, str]:
        """Изменение пароля пользователя"""
        await self.get_user_by_id(user_id)  # Проверяем существование пользователя
        
        self.db_manager.change_user_password(user_id, password_data.new_password)
        return {"message": "Пароль успешно изменен"}
    
    async def regenerate_password(self, user_id: int) -> Dict[str, str]:
        """Перегенерация пароля пользователя"""
        await self.get_user_by_id(user_id)  # Проверяем существование пользователя
        
        import secrets
        import string
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        self.db_manager.change_user_password(user_id, new_password)
        return {"new_password": new_password}
    
    async def toggle_admin_status(self, user_id: int) -> Dict[str, str]:
        """Переключение статуса администратора"""
        # Убедимся, что пользователь существует
        user = self.db_manager.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        new_status = self.db_manager.toggle_admin_status(user_id)
        if new_status is None:
            raise NotFoundError("Пользователь не найден")
        
        return {"message": f"Статус администратора изменен на {new_status}"}
    
    async def toggle_user_active_status(self, user_id: int) -> Dict[str, str]:
        """Переключение статуса активности пользователя"""
        # Убедимся, что пользователь существует
        user = self.db_manager.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("Пользователь не найден")

        new_status = self.db_manager.toggle_user_active_status(user_id)
        if new_status is None:
            raise NotFoundError("Пользователь не найден")
        
        return {"message": f"Статус активности изменен на {new_status}"}
    
    async def delete_user(self, user_id: int) -> Dict[str, str]:
        """Удаление пользователя"""
        success = self.db_manager.delete_user(user_id)
        if not success:
            raise ConflictError("Нельзя удалить администратора или пользователь не найден")
        
        return {"message": "Пользователь удален"}



