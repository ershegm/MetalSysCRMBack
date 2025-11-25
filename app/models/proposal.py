"""
Модели предложений
"""
from typing import Optional, Dict, Any
from pydantic import Field
from .base import BaseModel, IDMixin, TimestampMixin


class ProposalBase(BaseModel):
    """Базовая модель предложения"""
    company: str = Field("", description="Название компании")
    product_type: str = Field(..., description="Тип продукта")
    material: str = Field(..., description="Материал")
    material_grade: str = Field("", description="Марка материала")
    dimensions: str = Field(..., description="Размеры")
    selected_operations: str = Field(..., description="Выбранные операции")
    result: str = Field(..., description="Результат")
    status: str = Field("", description="Статус")
    priority: str = Field("", description="Приоритет")


class ProposalCreate(ProposalBase):
    """Модель для создания предложения"""
    pass


class ProposalUpdate(BaseModel):
    """Модель для обновления предложения"""
    company: Optional[str] = None
    product_type: Optional[str] = None
    material: Optional[str] = None
    material_grade: Optional[str] = None
    dimensions: Optional[str] = None
    selected_operations: Optional[str] = None
    result: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class ProposalResponse(ProposalBase, IDMixin, TimestampMixin):
    """Модель ответа с данными предложения"""
    user_id: int = Field(..., description="ID пользователя")
    created_at: str = Field(..., description="Дата создания")
    createdAt: str = Field(..., alias="createdAt", description="Дата создания (alias)")


class Proposal(ProposalBase, IDMixin, TimestampMixin):
    """Полная модель предложения (для внутреннего использования)"""
    user_id: int = Field(..., description="ID пользователя")
