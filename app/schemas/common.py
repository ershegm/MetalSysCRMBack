"""
Общие схемы для API
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Схема пагинированного ответа"""
    data: List[T] = Field(..., description="Список данных")
    total: int = Field(..., description="Общее количество записей")
    skip: int = Field(0, description="Пропущено записей")
    limit: int = Field(50, description="Лимит записей")


class ErrorResponse(BaseModel):
    """Схема ответа с ошибкой"""
    success: bool = Field(False, description="Успешность операции")
    error: str = Field(..., description="Текст ошибки")
    details: Optional[dict] = Field(None, description="Дополнительные детали ошибки")


class FileResponse(BaseModel):
    """Схема ответа с информацией о файле"""
    id: int = Field(..., description="ID файла")
    file_name: str = Field(..., description="Имя файла")
    file_path: Optional[str] = Field(None, description="Путь к файлу")
    file_type: str = Field(..., description="Тип файла")
    file_size: Optional[int] = Field(None, description="Размер файла в байтах")
    mime_type: Optional[str] = Field(None, description="MIME тип файла")
    version_number: Optional[int] = Field(1, description="Номер версии")
    is_current: bool = Field(True, description="Текущая версия")
    uploaded_at: Optional[str] = Field(None, description="Дата загрузки")
    uploaded_by: Optional[str] = Field(None, description="Кто загрузил")




