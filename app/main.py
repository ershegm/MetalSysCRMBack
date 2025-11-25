"""
Главный файл приложения - Enterprise архитектура
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core.config import settings
from .core.database import db_manager
from .api.middleware import setup_middleware
from .api.v1 import router as v1_router
from .core.exceptions import AppException, create_http_exception


def create_app() -> FastAPI:
    """Создает и настраивает приложение FastAPI"""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise API для управления металлоизделиями",
        debug=settings.debug
    )
    
    # Настройка middleware
    setup_middleware(app)
    
    # Инициализация базы данных
    db_manager.init_database()
    db_manager.migrate_users_table()  # Миграция таблицы пользователей
    db_manager.init_crm_tables()  # Инициализация таблиц CRM
    
    # Подключение роутов
    app.include_router(v1_router)
    
    # Подключение legacy роутов напрямую (без префикса)
    from .api.v1.legacy import router as legacy_router
    app.include_router(legacy_router)
    
    # Статическая раздача загруженных файлов
    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
    
    # Обработчик исключений приложения
    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        http_exception = create_http_exception(exc)
        return JSONResponse(
            status_code=http_exception.status_code,
            content=http_exception.detail
        )
    
    # Обработчик ошибок валидации
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors(), "body": exc.body}
        )
    
    # Корневой эндпоинт
    @app.get("/")
    async def root():
        return {
            "message": f"Добро пожаловать в {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "redoc": "/redoc"
        }
    
    # Эндпоинт здоровья
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.app_version,
            "database": "connected"
        }
    
    return app


# Создаем экземпляр приложения
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

