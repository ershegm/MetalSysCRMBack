"""
Правила и хелперы для валидации типов клиентов
"""
from __future__ import annotations

from typing import Dict, Any, List


CUSTOMER_TYPE_RULES: Dict[int, Dict[str, Any]] = {
    1: {
        "code": "LEGAL_ENTITY",
        "label": "Юр. лицо / ООО / АО",
        "description": "Организации, требующие полный комплект реквизитов",
        "required_fields": ["inn", "kpp", "ogrn"],
        "recommended_fields": ["manager_name", "manager_post", "address_legal"],
        "hidden_fields": [],
    },
    2: {
        "code": "ENTREPRENEUR",
        "label": "Индивидуальный предприниматель",
        "description": "ИП и самозанятые. КПП не используется",
        "required_fields": ["inn", "ogrn"],
        "recommended_fields": ["manager_name", "address_real"],
        "hidden_fields": ["kpp"],
    },
    3: {
        "code": "INDIVIDUAL",
        "label": "Физическое лицо",
        "description": "Частные лица без реквизитов",
        "required_fields": [],
        "recommended_fields": ["phone", "email"],
        "hidden_fields": ["inn", "kpp", "ogrn"],
    },
}


def get_customer_type_meta() -> List[Dict[str, Any]]:
    """Возвращает список правил типов для API"""
    meta: List[Dict[str, Any]] = []
    for type_id, rule in CUSTOMER_TYPE_RULES.items():
        meta.append(
            {
                "type_id": type_id,
                "code": rule["code"],
                "label": rule["label"],
                "description": rule.get("description"),
                "required_fields": rule["required_fields"],
                "recommended_fields": rule.get("recommended_fields", []),
                "hidden_fields": rule.get("hidden_fields", []),
            }
        )
    return meta


def validate_customer_fields(customer_type: int, payload: Dict[str, Any], *, allow_partial: bool = False) -> None:
    """
    Проверяет, что указан набор обязательных/запрещённых реквизитов для выбранного типа клиента.

    Args:
        customer_type: тип клиента (1,2,3)
        payload: словарь с данными
        allow_partial: если True, пропускаем проверку обязательных полей (используется при частичном обновлении)
    """
    rules = CUSTOMER_TYPE_RULES.get(int(customer_type))
    if not rules:
        return

    missing: List[str] = []
    if not allow_partial:
        for field in rules["required_fields"]:
            value = payload.get(field)
            if not value or not str(value).strip():
                missing.append(field)

    if missing:
        raise ValueError(
            f"Для типа клиента «{rules['label']}» нужно заполнить поля: {', '.join(missing)}"
        )

    # Очистим скрытые поля, чтобы не хранить лишние значения
    for field in rules.get("hidden_fields", []):
        if field in payload:
            payload[field] = ""

