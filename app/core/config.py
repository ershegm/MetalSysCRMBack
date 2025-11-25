"""
Конфигурация приложения с валидацией
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from functools import lru_cache

# Базовые пути проекта
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(APP_DIR)
DEFAULT_UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")


class Settings(BaseSettings):
    """Настройки приложения с валидацией"""
    
    # Основные настройки
    app_name: str = "Proflans Metal Host API"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Безопасность
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 360
    
    # База данных
    database_url: str = "sqlite:///./users.db"
    
    # OpenAI API
    openai_api_key: Optional[str] = None
    openai_api_url: str = "https://api.openai.com/v1/responses"
    prompt_id: Optional[str] = None
    prompt_version: Optional[str] = None
    max_output_tokens: int = 2000
    openai_connect_timeout: int = 15
    openai_read_timeout: int = 120
    
    # AI0 (Промежуточный ИИ для разделения запросов)
    prompt_id_ai0: Optional[str] = None
    prompt_version_ai0: Optional[str] = None
    
    # AI1 (Основной ИИ для обработки изделий)
    prompt_id_ai1: Optional[str] = None
    prompt_version_ai1: Optional[str] = None
    
    # Прокси настройки
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[str] = None
    
    # Файлы/загрузки
    max_files: int = 20
    max_file_size: int = 1024 * 1024 * 32 # 32 МБ
    max_prompt_length: int = 10000    # 10 000 символов
    app_dir: str = APP_DIR
    project_root: str = PROJECT_ROOT
    uploads_dir: str = DEFAULT_UPLOADS_DIR
    
    # Vector Store ID
    vector_store_id: str = "vs_68a5e1b86c708191821e26d95e95bccb"
    
    # CORS
    cors_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    
    @validator("cors_origins", "cors_allow_methods", "cors_allow_headers")
    def validate_cors_strings(cls, v):
        # Если это строка, возвращаем как есть
        if isinstance(v, str):
            return v
        # Если это список, конвертируем в строку
        if isinstance(v, list):
            return ",".join(v)
        return str(v)
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-this-in-production":
            import warnings
            warnings.warn("Используется дефолтный SECRET_KEY! Измените его в production!")
        return v
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        if not v:
            import warnings
            warnings.warn("OPENAI_API_KEY не установлен!")
        return v
    
    # Убираем валидацию прокси для простоты
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Игнорируем лишние поля


@lru_cache()
def get_settings() -> Settings:
    """Получить настройки приложения (кэшированные)"""
    settings_obj = Settings()
    # Обеспечиваем наличие директории загрузок
    os.makedirs(settings_obj.uploads_dir, exist_ok=True)
    return settings_obj


# Глобальный экземпляр настроек
settings = get_settings()
