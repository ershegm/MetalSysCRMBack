"""
Схемы API для Funnels
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class StageMetricsResponse(BaseModel):
    """Схема метрик по стадии"""
    stage_id: int = Field(..., description="ID стадии")
    deals_count: int = Field(0, description="Количество сделок")
    total_amount: float = Field(0, description="Общая сумма")
    avg_days_in_stage: float = Field(0, description="Среднее количество дней в стадии")
    conversion_percent: float = Field(0, description="Процент конверсии")
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StageResponse(BaseModel):
    """Схема ответа со стадией"""
    id: int = Field(..., description="ID стадии")
    funnel_id: int = Field(..., description="ID воронки")
    stage_id: str = Field(..., description="Идентификатор стадии")
    name: str = Field(..., description="Название стадии")
    label: Optional[str] = None
    description: Optional[str] = None
    color_text: Optional[str] = None
    color_bg: Optional[str] = None
    color_border: Optional[str] = None
    order_index: int = Field(0, description="Порядковый номер")
    is_system: bool = Field(False, description="Системная стадия")
    stage_semantic_id: str = Field("P", description="Семантический идентификатор: P, S, F")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metrics: Optional[StageMetricsResponse] = None
    
    class Config:
        from_attributes = True


class StageCreate(BaseModel):
    """Схема для создания стадии"""
    stage_id: str = Field(..., description="Идентификатор стадии")
    name: str = Field(..., min_length=1, max_length=100, description="Название стадии")
    label: Optional[str] = Field(None, max_length=100, description="Подпись стадии")
    description: Optional[str] = None
    color_text: Optional[str] = None
    color_bg: Optional[str] = None
    color_border: Optional[str] = None
    order_index: int = Field(0, description="Порядковый номер")
    is_system: bool = Field(False, description="Системная стадия")
    stage_semantic_id: str = Field("P", description="Семантический идентификатор: P, S, F")


class StageUpdate(BaseModel):
    """Схема для обновления стадии (все поля опциональны)"""
    name: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    color_text: Optional[str] = None
    color_bg: Optional[str] = None
    color_border: Optional[str] = None
    order_index: Optional[int] = None
    stage_semantic_id: Optional[str] = None


class FunnelBase(BaseModel):
    """Базовая схема воронки"""
    name: str = Field(..., min_length=1, max_length=255, description="Название воронки")
    description: Optional[str] = None
    is_default: bool = Field(False, description="Воронка по умолчанию")


class FunnelCreate(FunnelBase):
    """Схема для создания воронки"""
    pass


class FunnelUpdate(BaseModel):
    """Схема для обновления воронки (все поля опциональны)"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class FunnelResponse(FunnelBase):
    """Схема ответа с данными воронки"""
    id: int = Field(..., description="Уникальный идентификатор")
    external_id: Optional[str] = None
    is_active: bool = Field(True, description="Активна ли воронка")
    created_by_id: int = Field(..., description="ID создателя")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    stages: List[StageResponse] = Field(default_factory=list, description="Стадии воронки")
    
    class Config:
        from_attributes = True


class StageReorderRequest(BaseModel):
    """Схема для изменения порядка стадий"""
    stage_ids: List[int] = Field(..., description="Список ID стадий в новом порядке")




