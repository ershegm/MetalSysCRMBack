"""
Схемы API для Deals
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from .common import PaginatedResponse


class DealProductResponse(BaseModel):
    """Схема товара в сделке"""
    id: int = Field(..., description="ID товара")
    deal_id: int = Field(..., description="ID сделки")
    product_id: Optional[int] = None
    name: str = Field(..., description="Название товара")
    description: Optional[str] = None
    price: float = Field(..., description="Цена за единицу")
    quantity: float = Field(..., description="Количество")
    unit: Optional[str] = Field("шт", description="Единица измерения")
    discount_percent: float = Field(0, description="Процент скидки")
    tax_percent: float = Field(0, description="Процент налога")
    line_total: Optional[float] = Field(None, description="Итоговая сумма строки")
    added_at: Optional[datetime] = None
    added_by_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class DealFileResponse(BaseModel):
    """Схема файла сделки"""
    id: int = Field(..., description="ID файла")
    deal_id: int = Field(..., description="ID сделки")
    file_name: str = Field(..., description="Имя файла")
    file_path: Optional[str] = None
    file_type: str = Field(..., description="Тип файла: QUOTE, INVOICE, CONTRACT, SPECIFICATION, OTHER")
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    version_number: int = Field(1, description="Номер версии")
    is_current: bool = Field(True, description="Текущая версия")
    parent_version_id: Optional[int] = None
    uploaded_by_id: int = Field(..., description="ID пользователя, загрузившего файл")
    uploaded_at: Optional[datetime] = None
    is_deleted: bool = Field(False, description="Удалён ли файл")
    
    class Config:
        from_attributes = True


class DealCommentResponse(BaseModel):
    """Схема комментария к сделке"""
    id: int = Field(..., description="ID комментария")
    deal_id: int = Field(..., description="ID сделки")
    author_id: int = Field(..., description="ID автора")
    text: str = Field(..., description="Текст комментария")
    formatted_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_deleted: bool = Field(False, description="Удалён ли комментарий")
    parent_comment_id: Optional[int] = None
    author: Optional[dict] = None  # Обогащённое поле с данными автора
    
    class Config:
        from_attributes = True


class DealHistoryResponse(BaseModel):
    """Схема записи истории изменений сделки"""
    id: int = Field(..., description="ID записи истории")
    deal_id: int = Field(..., description="ID сделки")
    field_name: str = Field(..., description="Название поля")
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_type: str = Field(..., description="Тип изменения: CREATE, UPDATE, DELETE, STAGE_CHANGE, FILE_ADDED")
    changed_by_id: int = Field(..., description="ID пользователя, внесшего изменение")
    changed_at: Optional[datetime] = None
    changed_by: Optional[dict] = None  # Обогащённое поле с данными пользователя
    
    class Config:
        from_attributes = True


class DealParticipantResponse(BaseModel):
    """Схема участника сделки"""
    id: int = Field(..., description="ID участника")
    deal_id: int = Field(..., description="ID сделки")
    contact_id: Optional[int] = None
    user_id: Optional[int] = None
    participant_type: str = Field(..., description="Тип участника: PARTICIPANT, OBSERVER, APPROVER")
    joined_at: Optional[datetime] = None
    contact: Optional[dict] = None  # Обогащённое поле с данными контакта
    user: Optional[dict] = None  # Обогащённое поле с данными пользователя
    
    class Config:
        from_attributes = True


class FunnelReference(BaseModel):
    """Схема ссылки на воронку"""
    id: int = Field(..., description="ID воронки")
    name: str = Field(..., description="Название воронки")


class StageReference(BaseModel):
    """Схема ссылки на стадию"""
    id: int = Field(..., description="ID стадии")
    stage_id: str = Field(..., description="Идентификатор стадии")
    name: str = Field(..., description="Название стадии")
    label: Optional[str] = None
    order_index: int = Field(0, description="Порядковый номер")


class DealBase(BaseModel):
    """Базовая схема сделки"""
    title: str = Field(..., min_length=1, max_length=255, description="Название сделки")
    description: Optional[str] = None
    deal_type: str = Field("SALE", description="Тип сделки: SALE, PARTNERSHIP, SERVICE, CUSTOM")
    funnel_id: int = Field(..., description="ID воронки")
    stage_id: int = Field(..., description="ID стадии")
    amount: float = Field(0, description="Сумма сделки")
    currency_id: str = Field("RUB", description="Валюта")
    probability_percent: int = Field(50, description="Вероятность закрытия (%)")
    is_manual_amount: bool = Field(False, description="Ручной ввод суммы")
    tax_value: float = Field(0, description="Налог")
    start_date: Optional[date] = None
    close_date: Optional[date] = None
    company_id: Optional[int] = None
    primary_contact_id: Optional[int] = None
    responsible_user_id: int = Field(..., description="ID ответственного менеджера")
    is_public: bool = Field(True, description="Публичная сделка")
    is_recurring: bool = Field(False, description="Регулярная сделка")
    recurrence_pattern: Optional[str] = None
    source_id: Optional[str] = None
    source_description: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None


class DealCreate(DealBase):
    """Схема для создания сделки"""
    pass


class DealUpdate(BaseModel):
    """Схема для обновления сделки (все поля опциональны)"""
    title: Optional[str] = None
    description: Optional[str] = None
    deal_type: Optional[str] = None
    funnel_id: Optional[int] = None
    stage_id: Optional[int] = None
    amount: Optional[float] = None
    currency_id: Optional[str] = None
    probability_percent: Optional[int] = None
    is_manual_amount: Optional[bool] = None
    tax_value: Optional[float] = None
    start_date: Optional[date] = None
    close_date: Optional[date] = None
    company_id: Optional[int] = None
    primary_contact_id: Optional[int] = None
    responsible_user_id: Optional[int] = None
    is_closed: Optional[bool] = None
    is_public: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    source_id: Optional[str] = None
    source_description: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None


class DealResponse(DealBase):
    """Схема ответа с данными сделки"""
    id: int = Field(..., description="Уникальный идентификатор")
    external_id: Optional[str] = None
    deal_number: str = Field(..., description="Номер сделки")
    is_closed: bool = Field(False, description="Закрыта ли сделка")
    is_new: bool = Field(True, description="Новая сделка")
    is_return_customer: bool = Field(False, description="Возвратный клиент")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    moved_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    modified_by_id: Optional[int] = None
    moved_by_id: Optional[int] = None
    last_activity_by_id: Optional[int] = None
    originator_id: Optional[str] = None
    origin_id: Optional[str] = None
    
    # Связанные объекты
    funnel: Optional[FunnelReference] = None
    stage: Optional[StageReference] = None
    company: Optional[dict] = None
    primary_contact: Optional[dict] = None
    responsible_user: Optional[dict] = None
    
    # Вложенные объекты
    products: List[DealProductResponse] = Field(default_factory=list)
    files: List[DealFileResponse] = Field(default_factory=list)
    comments: List[DealCommentResponse] = Field(default_factory=list)
    participants: List[DealParticipantResponse] = Field(default_factory=list)
    history: List[DealHistoryResponse] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class DealListResponse(PaginatedResponse[DealResponse]):
    """Схема списка сделок с пагинацией"""
    pass




