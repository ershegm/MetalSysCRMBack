"""
Схемы API для Customers
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, model_validator
from .common import PaginatedResponse
from ..utils.customer_rules import CUSTOMER_TYPE_RULES


class CustomerContactSchema(BaseModel):
    """Схема контакта клиента"""
    id: Optional[int] = None
    contact_type: str = Field(..., description="Тип контакта: PHONE, EMAIL, WEB, IM")
    value_type: Optional[str] = Field(None, description="Тип значения: WORK, HOME, MAILING")
    value: str = Field(..., description="Значение контакта")
    is_primary: bool = Field(False, description="Основной контакт")


class CustomerFileSchema(BaseModel):
    """Схема файла клиента"""
    id: Optional[int] = None
    file_name: str = Field(..., description="Имя файла")
    file_path: Optional[str] = None
    file_type: str = Field(..., description="Тип файла: AGREEMENT, INVOICE, SPECIFICATION, OTHER")
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by_id: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    version_number: Optional[int] = 1


class CustomerBase(BaseModel):
    """Базовая схема клиента"""
    name: str = Field(..., min_length=1, max_length=255, description="Название компании")
    customer_type: int = Field(1, description="Тип клиента: 1=LEGAL_ENTITY, 2=ENTREPRENEUR, 3=INDIVIDUAL")
    email: Optional[str] = Field("", description="Email адрес")
    phone: Optional[str] = Field("", description="Номер телефона")
    address_legal: Optional[str] = Field("", description="Юридический адрес")
    address_real: Optional[str] = Field("", description="Фактический адрес")
    inn: Optional[str] = Field("", description="ИНН")
    kpp: Optional[str] = Field("", description="КПП")
    ogrn: Optional[str] = Field("", description="ОГРН")
    agreement: Optional[str] = Field("", description="Договор/соглашение")
    manager_name: Optional[str] = Field("", description="Имя менеджера")
    manager_post: Optional[str] = Field("", description="Должность менеджера")
    notes: Optional[str] = Field("", description="Заметки")
    currency_id: Optional[str] = Field("RUB", description="Валюта")
    annual_revenue: Optional[float] = None
    employees_count: Optional[int] = None
    industry: Optional[str] = None

    @model_validator(mode="after")
    def validate_type_specific_fields(cls, values: "CustomerBase"):
        customer_type = values.customer_type
        rules = CUSTOMER_TYPE_RULES.get(int(customer_type), None)
        if not rules:
            return values

        missing = []
        for field in rules["required_fields"]:
            value = getattr(values, field, None)
            if not value or not str(value).strip():
                missing.append(field)

        if missing:
            raise ValueError(
                f"Для типа клиента «{rules['label']}» нужно заполнить поля: {', '.join(missing)}"
            )

        for field in rules.get("hidden_fields", []):
            setattr(values, field, "")

        return values


class CustomerCreate(CustomerBase):
    """Схема для создания клиента"""
    contacts: Optional[List[CustomerContactSchema]] = Field(default_factory=list)
    files: Optional[List[CustomerFileSchema]] = Field(default_factory=list)


class CustomerUpdate(BaseModel):
    """Схема для обновления клиента (все поля опциональны)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    customer_type: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_legal: Optional[str] = None
    address_real: Optional[str] = None
    inn: Optional[str] = None
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    agreement: Optional[str] = None
    manager_name: Optional[str] = None
    manager_post: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    currency_id: Optional[str] = None
    annual_revenue: Optional[float] = None
    employees_count: Optional[int] = None
    industry: Optional[str] = None
    contacts: Optional[List[CustomerContactSchema]] = None
    files: Optional[List[CustomerFileSchema]] = None


class CustomerResponse(CustomerBase):
    """Схема ответа с данными клиента"""
    id: int = Field(..., description="Уникальный идентификатор")
    external_id: Optional[str] = None
    is_active: bool = Field(True, description="Активен ли клиент")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    modified_by_id: Optional[int] = None
    contacts: List[CustomerContactSchema] = Field(default_factory=list)
    files: List[CustomerFileSchema] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class CustomerListResponse(PaginatedResponse[CustomerResponse]):
    """Схема списка клиентов с пагинацией"""
    pass


class CustomerTypeRuleSchema(BaseModel):
    """Описание правил для типа клиента"""
    type_id: int
    code: str
    label: str
    description: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)
    recommended_fields: List[str] = Field(default_factory=list)
    hidden_fields: List[str] = Field(default_factory=list)


class CustomerMetaResponse(BaseModel):
    """Ответ с метаданными типов клиентов"""
    types: List[CustomerTypeRuleSchema]




