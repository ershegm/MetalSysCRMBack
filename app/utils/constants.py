"""
Константы для CRM системы
"""
from typing import Dict

# Системные стадии воронки по умолчанию
SYSTEM_STAGES = {
    "prospect": {
        "stage_id": "prospect",
        "name": "Первичный контакт",
        "label": "Первичный контакт",
        "color_text": "text-slate-800",
        "color_bg": "bg-slate-100",
        "color_border": "border-slate-400",
        "order_index": 0,
        "is_system": True,
        "stage_semantic_id": "P",
    },
    "negotiation": {
        "stage_id": "negotiation",
        "name": "Переговоры",
        "label": "Переговоры",
        "color_text": "text-blue-800",
        "color_bg": "bg-blue-100",
        "color_border": "border-blue-400",
        "order_index": 1,
        "is_system": True,
        "stage_semantic_id": "P",
    },
    "decision": {
        "stage_id": "decision",
        "name": "Принятие решения",
        "label": "Принятие решения",
        "color_text": "text-amber-800",
        "color_bg": "bg-amber-100",
        "color_border": "border-amber-400",
        "order_index": 2,
        "is_system": True,
        "stage_semantic_id": "P",
    },
    "payment": {
        "stage_id": "payment",
        "name": "Оплата",
        "label": "Оплата",
        "color_text": "text-purple-800",
        "color_bg": "bg-purple-100",
        "color_border": "border-purple-400",
        "order_index": 3,
        "is_system": True,
        "stage_semantic_id": "P",
    },
    "done": {
        "stage_id": "done",
        "name": "Выполнено",
        "label": "Выполнено",
        "color_text": "text-green-800",
        "color_bg": "bg-green-100",
        "color_border": "border-green-400",
        "order_index": 4,
        "is_system": True,
        "stage_semantic_id": "S",
    },
}

# Дефолтные значения
DEFAULT_FUNNEL_NAME = "Основная воронка"
DEFAULT_FUNNEL_DESCRIPTION = "Стандартная воронка продаж"
DEFAULT_CURRENCY = "RUB"
DEFAULT_DEAL_TYPE = "SALE"
DEFAULT_PROBABILITY_PERCENT = 50

# Цвета для стадий (для создания пользовательских стадий)
STAGE_COLORS = [
    {"text": "text-slate-800", "bg": "bg-slate-100", "border": "border-slate-400"},
    {"text": "text-blue-800", "bg": "bg-blue-100", "border": "border-blue-400"},
    {"text": "text-amber-800", "bg": "bg-amber-100", "border": "border-amber-400"},
    {"text": "text-purple-800", "bg": "bg-purple-100", "border": "border-purple-400"},
    {"text": "text-green-800", "bg": "bg-green-100", "border": "border-green-400"},
    {"text": "text-red-800", "bg": "bg-red-100", "border": "border-red-400"},
    {"text": "text-orange-800", "bg": "bg-orange-100", "border": "border-orange-400"},
]





