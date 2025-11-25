"""
Pydantic модели для валидации данных contacts (JSON)
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from .base import BaseModel as AppBaseModel


class ContactCommunication(BaseModel):
    """Модель коммуникации контакта"""
    id: Optional[int] = None
    comm_type: str = Field(..., description="Тип коммуникации: PHONE, EMAIL, IM, TELEGRAM, WHATSAPP")
    value_type: Optional[str] = Field(None, description="Тип значения: WORK, HOME, MAILING")
    value: str = Field(..., description="Значение коммуникации")
    is_primary: bool = Field(False, description="Основная коммуникация")


class ContactModel(AppBaseModel):
    """Полная модель контакта (для валидации JSON)"""
    id: int = Field(..., description="Уникальный идентификатор")
    external_id: Optional[str] = Field(None, description="Внешний идентификатор")
    
    # ФИО (legacy поле name для обратной совместимости)
    name: Optional[str] = Field("", description="Полное имя (legacy)")
    first_name: Optional[str] = Field("", description="Имя")
    middle_name: Optional[str] = Field("", description="Отчество")
    last_name: Optional[str] = Field("", description="Фамилия")
    honorific: Optional[str] = Field(None, description="Обращение: MR, MRS, MS, DR, PROF")
    
    # Связи
    company_id: Optional[int] = Field(None, description="ID компании (customer)")
    responsible_user_id: Optional[int] = Field(None, description="ID ответственного менеджера")
    
    # Дополнительные данные
    birthdate: Optional[str] = Field(None, description="Дата рождения (YYYY-MM-DD)")
    position: Optional[str] = Field("", description="Должность")
    department: Optional[str] = Field("", description="Отдел")
    photo_url: Optional[str] = Field(None, description="URL фотографии")
    
    # Контакты (legacy поля для обратной совместимости)
    email: Optional[str] = Field("", description="Email адрес")
    phone: Optional[str] = Field("", description="Номер телефона")
    
    # Управление
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    modified_by_id: Optional[int] = None
    is_active: bool = Field(True, description="Активен ли контакт")
    
    # Статистика
    deals_count: int = Field(0, description="Количество сделок")
    last_activity_at: Optional[datetime] = None
    
    # Массивы для множественных коммуникаций и тегов
    communications: List[ContactCommunication] = Field(default_factory=list, description="Множественные коммуникации")
    tags: List[str] = Field(default_factory=list, description="Теги для категоризации")
    
    # Обогащённые поля (заполняются при чтении)
    company_name: Optional[str] = Field(None, description="Название компании (обогащённое)")
    responsible_name: Optional[str] = Field(None, description="Имя ответственного (обогащённое)")




