"""
Middleware для приложения
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from ..core.config import settings
from ..core.exceptions import create_http_exception, AppException

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Логируем входящий запрос
        logger.info(f"Входящий запрос: {request.method} {request.url}")
        
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Вычисляем время обработки
        process_time = time.time() - start_time
        
        # Логируем ответ
        logger.info(
            f"Ответ: {response.status_code} - "
            f"Время обработки: {process_time:.4f}s"
        )
        
        # Добавляем заголовок с временем обработки
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware для обработки ошибок"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            logger.error(f"Ошибка приложения: {e.message}", exc_info=True)
            http_exception = create_http_exception(e)
            return Response(
                content=http_exception.detail,
                status_code=http_exception.status_code,
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}", exc_info=True)
            import json
            return Response(
                content=json.dumps({"message": "Внутренняя ошибка сервера", "details": str(e)}),
                status_code=500,
                media_type="application/json"
            )


def setup_middleware(app):
    """Настройка middleware для приложения"""
    
    # CORS middleware - ДОЛЖЕН БЫТЬ ПЕРВЫМ для правильной обработки preflight запросов
    # Для разработки используем явные localhost origins, так как allow_credentials=True
    # несовместим с allow_origins=["*"]
    allow_origins = [
        "http://localhost:8080",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://192.168.56.1:8080",
        "http://192.168.56.1:3000",
        "http://192.168.56.1:5173",
    ]
    
    # CORS middleware должен быть первым
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Логирование
    app.add_middleware(LoggingMiddleware)
    
    # Обработка ошибок
    app.add_middleware(ErrorHandlingMiddleware)

