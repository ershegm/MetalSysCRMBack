"""
Базовые модели
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    """Базовая модель с общими настройками"""
    
    class Config:
        from_attributes = True  # Заменено orm_mode на from_attributes для Pydantic v2
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True


class TimestampMixin(BaseModel):
    """Mixin для временных меток"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class IDMixin(BaseModel):
    """Mixin для ID"""
    id: int = Field(..., description="Уникальный идентификатор")

