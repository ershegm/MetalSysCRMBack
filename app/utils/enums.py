"""
Enum типы для CRM системы
"""
from enum import Enum


class CustomerType(str, Enum):
    """Типы клиентов"""
    LEGAL_ENTITY = "LEGAL_ENTITY"  # Юридическое лицо (type: 1)
    ENTREPRENEUR = "ENTREPRENEUR"  # ИП (type: 2)
    INDIVIDUAL = "INDIVIDUAL"  # Физическое лицо (type: 3)


class DealType(str, Enum):
    """Типы сделок"""
    SALE = "SALE"
    PARTNERSHIP = "PARTNERSHIP"
    SERVICE = "SERVICE"
    CUSTOM = "CUSTOM"


class FileType(str, Enum):
    """Типы файлов"""
    QUOTE = "QUOTE"  # Коммерческое предложение
    INVOICE = "INVOICE"  # Счёт
    CONTRACT = "CONTRACT"  # Договор
    SPECIFICATION = "SPECIFICATION"  # Спецификация
    OTHER = "OTHER"  # Другое


class ContactType(str, Enum):
    """Типы контактов/коммуникаций"""
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    IM = "IM"
    TELEGRAM = "TELEGRAM"
    WHATSAPP = "WHATSAPP"
    WEB = "WEB"


class ParticipantType(str, Enum):
    """Типы участников сделки"""
    PARTICIPANT = "PARTICIPANT"
    OBSERVER = "OBSERVER"
    APPROVER = "APPROVER"


class StageSemanticId(str, Enum):
    """Семантический идентификатор стадии"""
    P = "P"  # Процесс (в работе)
    S = "S"  # Успех (завершена успешно)
    F = "F"  # Отказ (завершена отказом)


class ChangeType(str, Enum):
    """Типы изменений в истории"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STAGE_CHANGE = "STAGE_CHANGE"
    FILE_ADDED = "FILE_ADDED"


# Маппинг типов клиентов (для обратной совместимости)
CUSTOMER_TYPE_MAPPING = {
    1: CustomerType.LEGAL_ENTITY,
    2: CustomerType.ENTREPRENEUR,
    3: CustomerType.INDIVIDUAL,
    "1": CustomerType.LEGAL_ENTITY,
    "2": CustomerType.ENTREPRENEUR,
    "3": CustomerType.INDIVIDUAL,
}

# Обратный маппинг
CUSTOMER_TYPE_TO_INT = {
    CustomerType.LEGAL_ENTITY: 1,
    CustomerType.ENTREPRENEUR: 2,
    CustomerType.INDIVIDUAL: 3,
}





