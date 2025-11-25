"""
Схемы API для Contacts
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from .common import PaginatedResponse


class ContactCommunicationSchema(BaseModel):
    """Схема коммуникации контакта"""
    id: Optional[int] = None
    comm_type: str = Field(..., description="Тип коммуникации: PHONE, EMAIL, IM, TELEGRAM, WHATSAPP")
    value_type: Optional[str] = Field(None, description="Тип значения: WORK, HOME, MAILING")
    value: str = Field(..., description="Значение коммуникации")
    is_primary: bool = Field(False, description="Основная коммуникация")


class CompanyReference(BaseModel):
    """Схема ссылки на компанию"""
    id: int = Field(..., description="ID компании")
    name: str = Field(..., description="Название компании")


class UserReference(BaseModel):
    """Схема ссылки на пользователя"""
    id: int = Field(..., description="ID пользователя")
    name: str = Field(..., description="Имя пользователя")


class ContactBase(BaseModel):
    """Базовая схема контакта"""
    first_name: str = Field(..., min_length=1, max_length=100, description="Имя")
    middle_name: Optional[str] = Field("", max_length=100, description="Отчество")
    last_name: str = Field(..., min_length=1, max_length=100, description="Фамилия")
    honorific: Optional[str] = Field(None, description="Обращение: MR, MRS, MS, DR, PROF")
    position: Optional[str] = Field("", description="Должность")
    department: Optional[str] = Field("", description="Отдел")
    birthdate: Optional[str] = Field(None, description="Дата рождения (YYYY-MM-DD)")
    photo_url: Optional[str] = Field(None, description="URL фотографии")
    company_id: Optional[int] = Field(None, description="ID компании")
    responsible_user_id: Optional[int] = Field(None, description="ID ответственного менеджера")


class ContactCreate(ContactBase):
    """Схема для создания контакта"""
    # Для обратной совместимости
    name: Optional[str] = Field("", description="Полное имя (legacy)")
    email: Optional[str] = Field("", description="Email адрес")
    phone: Optional[str] = Field("", description="Номер телефона")
    communications: Optional[List[ContactCommunicationSchema]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)


class ContactUpdate(BaseModel):
    """Схема для обновления контакта (все поля опциональны)"""
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    honorific: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    birthdate: Optional[str] = None
    photo_url: Optional[str] = None
    company_id: Optional[int] = None
    responsible_user_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    communications: Optional[List[ContactCommunicationSchema]] = None
    tags: Optional[List[str]] = None


class ContactResponse(ContactBase):
    """Схема ответа с данными контакта"""
    id: int = Field(..., description="Уникальный идентификатор")
    external_id: Optional[str] = None
    is_active: bool = Field(True, description="Активен ли контакт")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    modified_by_id: Optional[int] = None
    deals_count: int = Field(0, description="Количество сделок")
    last_activity_at: Optional[datetime] = None
    communications: List[ContactCommunicationSchema] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Обогащённые поля
    company: Optional[CompanyReference] = None
    responsible_user: Optional[UserReference] = None
    company_name: Optional[str] = None
    responsible_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class ContactListResponse(PaginatedResponse[ContactResponse]):
    """Схема списка контактов с пагинацией"""
    pass




