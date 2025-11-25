"""
Pydantic модели для валидации данных customers (JSON)
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from .base import BaseModel as AppBaseModel


class CustomerContact(BaseModel):
    """Модель контакта клиента"""
    id: Optional[int] = None
    contact_type: str = Field(..., description="Тип контакта: PHONE, EMAIL, WEB, IM")
    value_type: Optional[str] = Field(None, description="Тип значения: WORK, HOME, MAILING")
    value: str = Field(..., description="Значение контакта")
    is_primary: bool = Field(False, description="Основной контакт")


class CustomerFile(BaseModel):
    """Модель файла клиента"""
    id: Optional[int] = None
    file_name: str = Field(..., description="Имя файла")
    file_path: Optional[str] = None
    file_type: str = Field(..., description="Тип файла: AGREEMENT, INVOICE, SPECIFICATION, OTHER")
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    version_number: Optional[int] = 1
    is_deleted: bool = Field(False, description="Удалён ли файл")


class CustomerModel(AppBaseModel):
    """Полная модель клиента (для валидации JSON)"""
    id: int = Field(..., description="Уникальный идентификатор")
    external_id: Optional[str] = Field(None, description="Внешний идентификатор")
    name: str = Field(..., min_length=1, max_length=255, description="Название компании")
    customer_type: int = Field(1, description="Тип клиента: 1=LEGAL_ENTITY, 2=ENTREPRENEUR, 3=INDIVIDUAL")
    
    # Контакты (legacy поля для обратной совместимости)
    email: Optional[str] = Field("", description="Email адрес")
    phone: Optional[str] = Field("", description="Номер телефона")
    
    # Адреса
    address_legal: Optional[str] = Field("", description="Юридический адрес")
    address_real: Optional[str] = Field("", description="Фактический адрес")
    
    # Реквизиты (для юридических лиц и ИП)
    inn: Optional[str] = Field("", description="ИНН")
    kpp: Optional[str] = Field("", description="КПП")
    ogrn: Optional[str] = Field("", description="ОГРН")
    
    # Дополнительные поля
    agreement: Optional[str] = Field("", description="Договор/соглашение")
    manager_name: Optional[str] = Field("", description="Имя менеджера")
    manager_post: Optional[str] = Field("", description="Должность менеджера")
    notes: Optional[str] = Field("", description="Заметки")
    
    # Новые поля из архитектуры
    is_active: bool = Field(True, description="Активен ли клиент")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    modified_by_id: Optional[int] = None
    
    # Массивы для множественных контактов и файлов
    contacts: List[CustomerContact] = Field(default_factory=list, description="Множественные контакты")
    files: List[CustomerFile] = Field(default_factory=list, description="Файлы клиента")
    
    # Дополнительные поля из архитектуры
    currency_id: Optional[str] = Field("RUB", description="Валюта")
    annual_revenue: Optional[float] = None
    employees_count: Optional[int] = None
    industry: Optional[str] = None
    
    @validator('customer_type')
    def validate_customer_type(cls, v):
        """Валидация типа клиента"""
        if v not in (1, 2, 3):
            raise ValueError('customer_type должен быть 1, 2 или 3')
        return v
    
    @validator('inn')
    def validate_inn_if_present(cls, v):
        """Валидация ИНН если указан"""
        if v and v.strip():
            from ..utils.validators import validate_inn
            if not validate_inn(v):
                raise ValueError('Некорректный ИНН')
        return v or ""
    
    @validator('kpp')
    def validate_kpp_if_present(cls, v):
        """Валидация КПП если указан"""
        if v and v.strip():
            from ..utils.validators import validate_kpp
            if not validate_kpp(v):
                raise ValueError('Некорректный КПП')
        return v or ""
    
    @validator('ogrn')
    def validate_ogrn_if_present(cls, v):
        """Валидация ОГРН если указан"""
        if v and v.strip():
            from ..utils.validators import validate_ogrn
            if not validate_ogrn(v):
                raise ValueError('Некорректный ОГРН')
        return v or ""




