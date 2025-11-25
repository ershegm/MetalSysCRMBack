"""
Кастомные исключения приложения
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(Exception):
    """Базовое исключение приложения"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    """Ошибка валидации данных"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class AuthenticationError(AppException):
    """Ошибка аутентификации"""
    
    def __init__(self, message: str = "Ошибка аутентификации"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(AppException):
    """Ошибка авторизации"""
    
    def __init__(self, message: str = "Недостаточно прав"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(AppException):
    """Ресурс не найден"""
    
    def __init__(self, message: str = "Ресурс не найден"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictError(AppException):
    """Конфликт ресурсов"""
    
    def __init__(self, message: str = "Конфликт ресурсов"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class ExternalServiceError(AppException):
    """Ошибка внешнего сервиса"""
    
    def __init__(self, service: str, message: str = "Ошибка внешнего сервиса"):
        super().__init__(
            message=f"Ошибка сервиса {service}: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY
        )


def create_http_exception(exc: AppException) -> HTTPException:
    """Преобразует AppException в HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "message": exc.message,
            "details": exc.details
        }
    )

