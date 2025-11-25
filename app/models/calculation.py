"""
Модели расчетов
"""
from typing import Optional, List, Dict, Any
from pydantic import Field
from .base import BaseModel, IDMixin, TimestampMixin


class OperationBase(BaseModel):
    """Базовая модель операции"""
    service_id: int = Field(..., alias="serviceId", description="ID услуги")
    variant_id: str = Field(..., alias="variantId", description="ID варианта")
    name: str = Field(..., description="Название операции")
    unit: str = Field(..., description="Единица измерения")
    price: float = Field(..., description="Цена")
    qty: float = Field(..., description="Количество")
    cost: float = Field(..., description="Стоимость")

    class Config:
        populate_by_name = True  # Разрешить использование alias и обычных имен


class CalculationProductBase(BaseModel):
    """Базовая модель изделия (сортамент)"""
    id: str = Field(..., description="UUID изделия")
    name: str = Field(..., description="Название изделия")
    material: str = Field(..., description="Материал")
    weight: float = Field(..., description="Вес, кг")
    price_per_kg: float = Field(..., alias="pricePerKg", description="Цена за кг, руб")
    quantity: int = Field(..., description="Количество")
    material_cost: float = Field(..., alias="materialCost", description="Стоимость материала, руб")
    processing_cost: float = Field(default=0.0, alias="processingCost", description="Стоимость обработки, руб")
    total_cost: float = Field(..., alias="totalCost", description="Общая стоимость, руб")
    markup: Optional[float] = Field(default=None, description="Процент наценки")
    operations: Optional[List[OperationBase]] = Field(default=None, description="Технологические операции")
    comment: Optional[str] = Field(default=None, description="Комментарий")
    is_ai_generated: Optional[bool] = Field(default=False, alias="isAIGenerated", description="Создано через AI")
    shape: Optional[str] = Field(default=None, description="Форма сортамента")
    dimensions: Optional[Dict[str, Any]] = Field(default=None, description="Размеры")
    tech_card: Optional[str] = Field(default=None, alias="techCard", description="Технологическая карта (deprecated)")

    class Config:
        populate_by_name = True  # Разрешить использование alias и обычных имен


class BlankBase(BaseModel):
    """Базовая модель заготовки"""
    id: str = Field(..., description="UUID заготовки")
    name: str = Field(..., description="Название заготовки")
    weight: float = Field(..., description="Вес, кг")
    price: float = Field(..., description="Цена, руб")
    quantity: int = Field(..., description="Количество")
    markup: float = Field(default=0.0, description="Процент наценки")
    sum: float = Field(..., description="Итоговая сумма с наценкой, руб")


class GlobalOperationBase(BaseModel):
    """Базовая модель глобальной операции (изделие)"""
    service_id: Optional[int] = Field(default=None, alias="serviceId", description="ID услуги")
    variant_id: Optional[str] = Field(default=None, alias="variantId", description="ID варианта")
    qty: Optional[float] = Field(default=None, description="Количество")
    cost: Optional[float] = Field(default=None, description="Стоимость операции (для расчета в истории)")

    class Config:
        populate_by_name = True


class CalculationBase(BaseModel):
    """Базовая модель расчета"""
    name: str = Field(..., description="Название изделия")
    assortments: List[CalculationProductBase] = Field(default_factory=list, description="Сортаменты")
    blanks: List[BlankBase] = Field(default_factory=list, description="Заготовки")
    global_operations: List[GlobalOperationBase] = Field(default_factory=list, alias="globalOperations", description="Глобальные операции")
    global_markup: float = Field(default=0.0, alias="globalMarkup", description="Глобальная наценка, %")
    global_markup_apply_to_assortments: bool = Field(default=True, alias="globalMarkupApplyToAssortments", description="Применять глобальную наценку к сортаментам")
    global_markup_apply_to_blanks: bool = Field(default=False, alias="globalMarkupApplyToBlanks", description="Применять глобальную наценку к заготовкам")
    global_markup_apply_to_operations: bool = Field(default=False, alias="globalMarkupApplyToOperations", description="Применять глобальную наценку к технологическим операциям")

    class Config:
        populate_by_name = True


class CalculationCreate(CalculationBase):
    """Модель для создания расчета"""
    pass


class CalculationUpdate(BaseModel):
    """Модель для обновления расчета"""
    name: Optional[str] = None
    assortments: Optional[List[CalculationProductBase]] = None
    blanks: Optional[List[BlankBase]] = None
    global_operations: Optional[List[GlobalOperationBase]] = Field(default=None, alias="globalOperations")
    global_markup: Optional[float] = Field(default=None, alias="globalMarkup")
    global_markup_apply_to_assortments: Optional[bool] = Field(default=None, alias="globalMarkupApplyToAssortments")
    global_markup_apply_to_blanks: Optional[bool] = Field(default=None, alias="globalMarkupApplyToBlanks")
    global_markup_apply_to_operations: Optional[bool] = Field(default=None, alias="globalMarkupApplyToOperations")

    class Config:
        populate_by_name = True


class CalculationResponse(CalculationBase, IDMixin, TimestampMixin):
    """Модель ответа с данными расчета"""
    pass


class Calculation(CalculationBase, IDMixin, TimestampMixin):
    """Полная модель расчета (для внутреннего использования)"""
    pass



