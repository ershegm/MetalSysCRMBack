"""
Legacy API роуты для обратной совместимости
"""
from fastapi import APIRouter, Depends, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List, Optional
import os
import json
from ..deps import get_auth_service, get_user_service, get_proposal_service, get_ai_service, get_file_service
from ...services.auth_service import AuthService
from ...services.user_service import UserService
from ...services.proposal_service import ProposalService
from ...core.security import get_current_user
from ...services.ai_service import AIService
from ...services.file_service import FileService
from ...models.user import UserLogin

router = APIRouter()

# Обработчик ошибок валидации будет добавлен в main.py

# Legacy роуты для обратной совместимости

# Аутентификация
@router.post("/api/auth/login")
async def login_legacy(
    user_credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Legacy: Вход пользователя"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Login attempt: login={user_credentials.login}, password_length={len(user_credentials.password)}")
    try:
        return await auth_service.authenticate_user(user_credentials)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise


@router.get("/api/auth/me")
async def get_current_user_info_legacy(
    current_user: dict = Depends(get_current_user)
):
    """Legacy: Получение информации о текущем пользователе"""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "is_admin": current_user["is_admin"]
    }


@router.get("/api/history")
async def get_history_legacy(
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Legacy: Получение истории предложений"""
    return await proposal_service.get_proposals()


@router.post("/api/history")
async def save_to_history_legacy(
    data: dict,
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Legacy: Сохранение предложения в историю"""
    from ...models.proposal import ProposalCreate
    
    proposal_data = ProposalCreate(
        company=data.get('company', ''),
        product_type=data.get('productType', ''),
        material=data.get('material', ''),
        material_grade=data.get('materialGrade', ''),
        dimensions=data.get('dimensions', '{}'),
        selected_operations=data.get('selectedOperations', '[]'),
        result=data.get('result', '{}')
    )
    
    return await proposal_service.create_proposal(proposal_data)


@router.put("/api/history/{proposal_id}")
async def update_history_item_legacy(
    proposal_id: int,
    data: dict,
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Legacy: Обновление предложения в истории"""
    from ...models.proposal import ProposalUpdate
    
    proposal_data = ProposalUpdate(
        company=data.get('company'),
        product_type=data.get('productType'),
        material=data.get('material'),
        material_grade=data.get('materialGrade'),
        dimensions=data.get('dimensions'),
        selected_operations=data.get('selectedOperations'),
        result=data.get('result'),
        status=data.get('status'),
        priority=data.get('priority')
    )
    
    return await proposal_service.update_proposal(proposal_id, proposal_data)


@router.delete("/api/history/{proposal_id}")
async def delete_history_item_legacy(
    proposal_id: int,
    proposal_service: ProposalService = Depends(get_proposal_service)
):
    """Legacy: Удаление предложения из истории"""
    return await proposal_service.delete_proposal(proposal_id)


@router.get("/api/materials")
async def get_materials_legacy():
    """Legacy: Получение списка материалов"""
    return {
        "materials": [
            {"id": 1, "name": "Сталь 3", "density": 7.85},
            {"id": 2, "name": "Сталь 20", "density": 7.85},
            {"id": 3, "name": "Чугун", "density": 7.2},
            {"id": 4, "name": "Алюминий", "density": 2.7}
        ]
    }


@router.get("/api/templates")
async def get_templates_legacy():
    """Legacy: Получение списка шаблонов"""
    return {
        "templates": [
            {"id": 1, "name": "Фланец", "description": "Стандартный фланец"},
            {"id": 2, "name": "Труба", "description": "Труба круглого сечения"},
            {"id": 3, "name": "Лист", "description": "Плоский лист"}
        ]
    }


# Legacy webhook - используем тот же код что и в новом API
@router.post("/api/webhook")
async def webhook_legacy(
    request: Request,
    gost_size: Optional[str] = Form(None),
    additional_requirements: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    ai_service: AIService = Depends(get_ai_service),
    file_service: FileService = Depends(get_file_service)
):
    """Legacy: Webhook для обработки AI запросов"""
    # Импортируем функцию из нового API
    from .ai import ai_webhook
    
    # Вызываем новую функцию
    return await ai_webhook(request, gost_size, additional_requirements, files, ai_service, file_service)


# ======================
# Prices (simple storage)
# ======================

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
BACKEND_ROOT = os.path.dirname(ROOT_DIR)  # backend/
PRICES_STORAGE_PATH = os.path.join(ROOT_DIR, 'prices.json')
PRICES_FOR_WORKS_STORAGE_PATH = os.path.join(BACKEND_ROOT, 'prices_for_works.json')
MATERIALS_SETTINGS_PATH = os.path.join(BACKEND_ROOT, 'prices_metal_materials.json')
CUSTOMERS_STORAGE_PATH = os.path.join(ROOT_DIR, 'customers.json')
CONTACTS_STORAGE_PATH = os.path.join(ROOT_DIR, 'contacts.json')
CATALOG_STORAGE_PATH = os.path.join(ROOT_DIR, 'catalog.json')
WAREHOUSE_STORAGE_PATH = os.path.join(ROOT_DIR, 'warehouse.json')
CALCULATIONS_STORAGE_PATH = os.path.join(ROOT_DIR, 'calculations.json')

def _read_prices() -> list:
    try:
        if os.path.exists(PRICES_STORAGE_PATH):
            with open(PRICES_STORAGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def _write_prices(items: list) -> None:
    try:
        with open(PRICES_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        # Игнорируем ошибки записи для простоты
        pass


@router.get("/api/prices")
async def get_prices_legacy():
    """Вернуть список прайсов из локального JSON хранилища."""
    return _read_prices()


@router.post("/api/prices/import")
async def import_prices_legacy(items: List[dict]):
    """Импорт прайс-листа. Полностью заменяет текущий список."""
    if not isinstance(items, list):
        return JSONResponse(status_code=400, content={"success": False, "error": "Invalid payload"})
    _write_prices(items)
    return {"success": True, "count": len(items)}


@router.post("/api/prices/add")
async def add_price_item(item: dict):
    """Добавить новый товар в прайс-лист."""
    try:
        # Проверяем обязательные поля
        required_fields = ['number', 'name', 'price']
        for field in required_fields:
            if field not in item or not item[field]:
                return JSONResponse(
                    status_code=400, 
                    content={"success": False, "error": f"Поле '{field}' обязательно"}
                )
        
        # Читаем текущий список
        current_items = _read_prices()
        
        # Проверяем, что номер не дублируется
        if any(existing_item.get('number') == item['number'] for existing_item in current_items):
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": f"Товар с номером '{item['number']}' уже существует"}
            )
        
        # Добавляем новый товар
        current_items.append(item)
        
        # Сохраняем обновленный список
        _write_prices(current_items)
        
        return {"success": True, "item": item, "count": len(current_items)}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при добавлении товара: {str(e)}"}
        )


# ======================
# Production Operations (prices_for_works.json)
# ======================

def _read_production_operations() -> list:
    try:
        if os.path.exists(PRICES_FOR_WORKS_STORAGE_PATH):
            with open(PRICES_FOR_WORKS_STORAGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Обеспечиваем новую структуру: Варианты + Колонки + Поля
                    data = _ensure_columns_structure(data)
                    return data
    except Exception:
        pass
    return []

def _convert_old_to_new_structure(old_data: list) -> list:
    """Конвертирует старую плоскую структуру в новую структуру с группировкой."""
    services_dict = {}
    for i, item in enumerate(old_data):
        service_name = item.get('Услуга', '')
        if service_name not in services_dict:
            services_dict[service_name] = {
                'id': len(services_dict),
                'Услуга': service_name,
                'Варианты': []
            }
        variant = {
            'id': f"{services_dict[service_name]['id']}-{len(services_dict[service_name]['Варианты'])}",
            'Диаметр (Ду)': item.get('Диаметр (Ду)'),
            'Исполнение': item.get('Исполнение'),
            'Цена': item.get('Цена'),
            'Единица измерения': item.get('Единица измерения'),
            'Примечание': item.get('Примечание')
        }
        services_dict[service_name]['Варианты'].append(variant)
    return list(services_dict.values())

def _ensure_columns_structure(data: list) -> list:
    """Гарантирует наличие схемы колонок ('Колонки') и переноса произвольных полей в 'Поля' у вариантов.
    Стандартные поля варианта: 'Цена', 'Единица измерения', 'Примечание', 'id'. Остальные считаются настраиваемыми.
    """
    modified = False
    new_data = []
    for service in data:
        service_copy = dict(service)
        variants = list(service_copy.get('Варианты', []))
        # Собираем все нестандартные ключи из вариантов
        standard_variant_keys = {'id', 'Цена', 'Единица измерения', 'Примечание', 'Поля'}
        custom_keys = []
        for v in variants:
            # ключи верхнего уровня (до миграции)
            for k in v.keys():
                if k not in standard_variant_keys:
                    custom_keys.append(k)
            # ключи внутри Поля (после миграции)
            fields = v.get('Поля') or {}
            for k in fields.keys():
                if k not in custom_keys:
                    custom_keys.append(k)
        # Уникальные ключи
        custom_keys_unique = []
        for k in custom_keys:
            if k not in custom_keys_unique:
                custom_keys_unique.append(k)
        # Если у услуги нет 'Колонки', формируем их из найденных ключей
        # Пустой список трактуем как осознанное отсутствие пользовательских колонок
        if 'Колонки' not in service_copy:
            service_copy['Колонки'] = [
                {
                    'key': _normalize_column_key(k),
                    'label': k,
                    'type': 'string'
                } for k in custom_keys_unique
            ]
            if custom_keys_unique:
                modified = True
        # Переносим значения в v['Поля']
        new_variants = []
        for v in variants:
            v_copy = dict(v)
            if 'Поля' not in v_copy:
                fields_obj = {}
                for k in list(v_copy.keys()):
                    if k not in standard_variant_keys:
                        fields_obj[_normalize_column_key(k)] = v_copy.pop(k)
                if fields_obj:
                    v_copy['Поля'] = fields_obj
                    modified = True
            new_variants.append(v_copy)
        service_copy['Варианты'] = new_variants
        new_data.append(service_copy)
    if modified:
        _write_production_operations(new_data)
    return new_data

def _normalize_column_key(label: str) -> str:
    # Превращаем человеческий ярлык в ключ: латиница/цифры/подчеркивания
    import re
    key = label.strip().lower()
    # Заменяем пробелы и скобки на подчеркивания
    key = re.sub(r"\s+", "_", key)
    key = key.replace('(', '').replace(')', '')
    # Удаляем прочие недопустимые символы
    key = re.sub(r"[^a-z0-9_а-яё]", "", key)
    return key

def _write_production_operations(items: list) -> None:
    try:
        with open(PRICES_FOR_WORKS_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


@router.get("/api/production-operations")
async def get_production_operations():
    """Вернуть список технологических операций производства (структурированный формат)."""
    return _read_production_operations()


@router.post("/api/production-operations/add-service")
async def add_production_service(service: dict):
    """Добавить новую услугу."""
    try:
        if 'Услуга' not in service or not service['Услуга']:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Поле 'Услуга' обязательно"}
            )
        
        current_services = _read_production_operations()
        max_id = max([s.get('id', -1) for s in current_services] + [-1])
        
        new_service = {
            'id': max_id + 1,
            'Услуга': service['Услуга'],
            'Варианты': service.get('Варианты', [])
        }
        
        current_services.append(new_service)
        _write_production_operations(current_services)
        
        return {"success": True, "item": new_service, "count": len(current_services)}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при добавлении услуги: {str(e)}"}
        )


@router.post("/api/production-operations/add-variant")
async def add_production_variant(payload: dict):
    """Добавить новый вариант к услуге."""
    try:
        service_id = payload.get('service_id')
        variant = payload.get('variant')
        
        if service_id is None or variant is None:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Необходимы service_id и variant"}
            )
        
        current_services = _read_production_operations()
        service = None
        service_index = None
        
        for i, s in enumerate(current_services):
            if s.get('id') == service_id:
                service = s
                service_index = i
                break
        
        if service is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Услуга с id={service_id} не найдена"}
            )
        
        # Генерируем id для варианта
        variant_id = f"{service_id}-{len(service.get('Варианты', []))}"
        variant['id'] = variant_id
        
        if 'Варианты' not in service:
            service['Варианты'] = []
        
        service['Варианты'].append(variant)
        current_services[service_index] = service
        _write_production_operations(current_services)
        
        return {"success": True, "variant": variant, "service": service}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при добавлении варианта: {str(e)}"}
        )


# Оставляем старый endpoint для обратной совместимости
@router.post("/api/production-operations/add")
async def add_production_operation(operation: dict):
    """Добавить новую технологическую операцию (legacy, создает услугу с одним вариантом)."""
    try:
        if 'Услуга' not in operation or not operation['Услуга']:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Поле 'Услуга' обязательно"}
            )
        
        current_services = _read_production_operations()
        max_id = max([s.get('id', -1) for s in current_services] + [-1])
        
        # Создаем вариант из старого формата
        variant = {
            'id': f"{max_id + 1}-0",
            'Диаметр (Ду)': operation.get('Диаметр (Ду)'),
            'Исполнение': operation.get('Исполнение'),
            'Цена': operation.get('Цена'),
            'Единица измерения': operation.get('Единица измерения'),
            'Примечание': operation.get('Примечание')
        }
        
        new_service = {
            'id': max_id + 1,
            'Услуга': operation['Услуга'],
            'Варианты': [variant]
        }
        
        current_services.append(new_service)
        _write_production_operations(current_services)
        
        return {"success": True, "item": new_service, "count": len(current_services)}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при добавлении операции: {str(e)}"}
        )


@router.post("/api/production-operations/edit-service")
async def edit_production_service(service: dict):
    """Редактировать услугу."""
    try:
        service_id = service.get('id')
        if service_id is None:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Поле 'id' обязательно для редактирования"}
            )
        
        current_services = _read_production_operations()
        found_index = None
        
        for i, s in enumerate(current_services):
            if s.get('id') == service_id:
                found_index = i
                break
        
        if found_index is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Услуга с id={service_id} не найдена"}
            )
        
        # Сохраняем существующие варианты, если они не переданы
        if 'Варианты' not in service:
            service['Варианты'] = current_services[found_index].get('Варианты', [])
        
        current_services[found_index] = service
        _write_production_operations(current_services)
        
        return {"success": True, "item": service}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при редактировании услуги: {str(e)}"}
        )


@router.post("/api/production-operations/edit-variant")
async def edit_production_variant(payload: dict):
    """Редактировать вариант услуги."""
    try:
        service_id = payload.get('service_id')
        variant_id = payload.get('variant_id')
        variant = payload.get('variant')
        
        if service_id is None or variant_id is None or variant is None:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Необходимы service_id, variant_id и variant"}
            )
        
        current_services = _read_production_operations()
        service = None
        service_index = None
        
        for i, s in enumerate(current_services):
            if s.get('id') == service_id:
                service = s
                service_index = i
                break
        
        if service is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Услуга с id={service_id} не найдена"}
            )
        
        variants = service.get('Варианты', [])
        variant_index = None
        
        for i, v in enumerate(variants):
            if v.get('id') == variant_id:
                variant_index = i
                break
        
        if variant_index is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Вариант с id={variant_id} не найден"}
            )
        
        variant['id'] = variant_id  # Сохраняем id
        variants[variant_index] = variant
        service['Варианты'] = variants
        current_services[service_index] = service
        _write_production_operations(current_services)
        
        return {"success": True, "variant": variant, "service": service}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при редактировании варианта: {str(e)}"}
        )


# Оставляем старый endpoint для обратной совместимости
@router.post("/api/production-operations/edit")
async def edit_production_operation(operation: dict):
    """Редактировать технологическую операцию (legacy)."""
    try:
        # Старая структура - конвертируем в работу с новой
        if 'Варианты' in operation:
            return await edit_production_service(operation)
        else:
            # Старый формат - пытаемся найти по id услуги или варианта
            operation_id = operation.get('id')
            if operation_id is None:
                return JSONResponse(
                    status_code=400, 
                    content={"success": False, "error": "Поле 'id' обязательно"}
                )
            
            # Проверяем формат id (может быть число или "0-0")
            if isinstance(operation_id, str) and '-' in str(operation_id):
                # Это вариант
                parts = str(operation_id).split('-')
                service_id = int(parts[0])
                variant_id = str(operation_id)
                return await edit_production_variant({
                    'service_id': service_id,
                    'variant_id': variant_id,
                    'variant': {
                        'Диаметр (Ду)': operation.get('Диаметр (Ду)'),
                        'Исполнение': operation.get('Исполнение'),
                        'Цена': operation.get('Цена'),
                        'Единица измерения': operation.get('Единица измерения'),
                        'Примечание': operation.get('Примечание')
                    }
                })
            else:
                # Это услуга
                return await edit_production_service(operation)
                
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при редактировании операции: {str(e)}"}
        )


@router.post("/api/production-operations/delete-service")
async def delete_production_service(payload: dict):
    """Удалить услугу."""
    try:
        service_id = payload.get('id')
        if service_id is None:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Поле 'id' обязательно для удаления"}
            )
        
        current_services = _read_production_operations()
        found_index = None
        
        for i, s in enumerate(current_services):
            if s.get('id') == service_id:
                found_index = i
                break
        
        if found_index is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Услуга с id={service_id} не найдена"}
            )
        
        removed_service = current_services.pop(found_index)
        _write_production_operations(current_services)
        
        return {"success": True, "item": removed_service, "count": len(current_services)}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при удалении услуги: {str(e)}"}
        )


@router.post("/api/production-operations/delete-variant")
async def delete_production_variant(payload: dict):
    """Удалить вариант услуги."""
    try:
        service_id = payload.get('service_id')
        variant_id = payload.get('variant_id')
        
        if service_id is None or variant_id is None:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Необходимы service_id и variant_id"}
            )
        
        current_services = _read_production_operations()
        service = None
        service_index = None
        
        for i, s in enumerate(current_services):
            if s.get('id') == service_id:
                service = s
                service_index = i
                break
        
        if service is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Услуга с id={service_id} не найдена"}
            )
        
        variants = service.get('Варианты', [])
        variant_index = None
        
        for i, v in enumerate(variants):
            if v.get('id') == variant_id:
                variant_index = i
                break
        
        if variant_index is None:
            return JSONResponse(
                status_code=404, 
                content={"success": False, "error": f"Вариант с id={variant_id} не найден"}
            )
        
        removed_variant = variants.pop(variant_index)
        service['Варианты'] = variants
        current_services[service_index] = service
        _write_production_operations(current_services)
        
        return {"success": True, "variant": removed_variant, "service": service}
        
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при удалении варианта: {str(e)}"}
        )


# Оставляем старый endpoint для обратной совместимости
@router.post("/api/production-operations/delete")
async def delete_production_operation(payload: dict):
    """Удалить технологическую операцию (legacy)."""
    try:
        operation_id = payload.get('id')
        if operation_id is None:
            return JSONResponse(
                status_code=400, 
                content={"success": False, "error": "Поле 'id' обязательно для удаления"}
            )
        
        # Проверяем формат id
        if isinstance(operation_id, str) and '-' in str(operation_id):
            # Это вариант
            parts = str(operation_id).split('-')
            service_id = int(parts[0])
            return await delete_production_variant({
                'service_id': service_id,
                'variant_id': operation_id
            })
        else:
            # Это услуга
            return await delete_production_service(payload)
            
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"success": False, "error": f"Ошибка при удалении операции: {str(e)}"}
        )


# ======================
# Customers (using CustomerService)
# ======================

from ...services.customer_service import CustomerService

customer_service = CustomerService()


@router.get('/api/customers/get_list')
async def customers_get_list_legacy():
    """Legacy: Получение списка клиентов"""
    customers, total = customer_service.get_all(skip=0, limit=1000)
    return {"success": True, "customers": customers}


@router.post('/api/customers/get_entry')
async def customers_get_entry_legacy(data: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Получение клиента по ID"""
    cid = data.get('customer_id')
    if cid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "customer_id required"})
    
    customer = customer_service.get_by_id(cid)
    if not customer:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
    
    return {"success": True, "customer": customer}


@router.post('/api/customers/add')
async def customers_add_legacy(payload: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Добавление клиента"""
    name = payload.get('name')
    if not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "name required"})
    
    try:
        customer_data = {
            'name': name,
            'customer_type': payload.get('type', payload.get('customer_type', 3)),
            'email': payload.get('email', ''),
            'phone': payload.get('phone', ''),
            'address_legal': payload.get('address_legal', ''),
            'address_real': payload.get('address_real', ''),
            'inn': payload.get('inn', ''),
            'kpp': payload.get('kpp', ''),
            'ogrn': payload.get('ogrn', ''),
            'agreement': payload.get('agreement', ''),
            'manager_name': payload.get('manager_name', ''),
            'manager_post': payload.get('manager_post', ''),
            'notes': payload.get('notes', ''),
        }
        customer = customer_service.create(customer_data, user_id=current_user.get('id'))
        return {"success": True, "customer_id": customer['id']}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@router.post('/api/customers/edit')
async def customers_edit_legacy(payload: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Редактирование клиента"""
    cid = payload.get('customer_id')
    name = payload.get('name')
    if cid is None or not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "customer_id and name required"})
    
    try:
        customer_data = {
            'name': name,
            'customer_type': payload.get('type', payload.get('customer_type')),
            'email': payload.get('email', ''),
            'phone': payload.get('phone', ''),
            'address_legal': payload.get('address_legal', ''),
            'address_real': payload.get('address_real', ''),
            'inn': payload.get('inn', ''),
            'kpp': payload.get('kpp', ''),
            'ogrn': payload.get('ogrn', ''),
            'agreement': payload.get('agreement', ''),
            'manager_name': payload.get('manager_name', ''),
            'manager_post': payload.get('manager_post', ''),
            'notes': payload.get('notes', ''),
        }
        customer = customer_service.update(cid, customer_data, user_id=current_user.get('id'))
        if not customer:
            return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
        return {"success": True}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@router.post('/api/customers/delete')
async def customers_delete_legacy(payload: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Удаление клиента"""
    cid = payload.get('customer_id')
    if cid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "customer_id required"})
    
    success = customer_service.delete(cid, soft=True)
    if not success:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
    return {"success": True}


# ======================
# Contacts (using ContactService)
# ======================

from ...services.contact_service import ContactService

contact_service = ContactService()


@router.get('/api/contacts/get_list')
async def contacts_get_list_legacy():
    """Legacy: Получение списка контактов"""
    contacts, total = contact_service.get_all(skip=0, limit=1000)
    return {"success": True, "contacts": contacts}


@router.post('/api/contacts/get_entry')
async def contacts_get_entry_legacy(data: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Получение контакта по ID"""
    cid = data.get('contact_id')
    if cid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "contact_id required"})
    
    contact = contact_service.get_by_id(cid)
    if not contact:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
    
    return {"success": True, "contact": contact}


@router.post('/api/contacts/add')
async def contacts_add_legacy(payload: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Добавление контакта"""
    name = payload.get('name')
    if not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "name required"})
    
    contact_data = {
        'name': name,
        'email': payload.get('email', ''),
        'phone': payload.get('phone', ''),
        'responsible_user_id': payload.get('responsible_id'),
        'company_id': payload.get('company_id'),
        'tags': payload.get('tags', []),
    }
    contact = contact_service.create(contact_data, user_id=current_user.get('id'))
    return {"success": True, "contact": contact, "contact_id": contact['id']}


@router.post('/api/contacts/edit')
async def contacts_edit_legacy(payload: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Редактирование контакта"""
    cid = payload.get('id')
    name = payload.get('name')
    if cid is None or not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "id and name required"})
    
    contact_data = {
        'name': name,
        'email': payload.get('email'),
        'phone': payload.get('phone'),
        'responsible_user_id': payload.get('responsible_id'),
        'company_id': payload.get('company_id'),
        'tags': payload.get('tags'),
    }
    # Удаляем None значения
    contact_data = {k: v for k, v in contact_data.items() if v is not None}
    
    contact = contact_service.update(cid, contact_data, user_id=current_user.get('id'))
    if not contact:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
    
    return {"success": True, "contact": contact}


@router.post('/api/contacts/delete')
async def contacts_delete_legacy(payload: dict, current_user: dict = Depends(get_current_user)):
    """Legacy: Удаление контакта"""
    cid = payload.get('contact_id')
    if cid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "contact_id required"})
    
    success = contact_service.delete(cid)
    if not success:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
    return {"success": True}


# ======================
# Catalog (products storage)
# ======================

def _read_catalog() -> list:
    try:
        if os.path.exists(CATALOG_STORAGE_PATH):
            with open(CATALOG_STORAGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def _write_catalog(items: list) -> None:
    try:
        with open(CATALOG_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _next_product_id(items: list) -> int:
    return (max([p.get('id', 0) for p in items] + [0]) + 1)


@router.get('/api/catalog/get_list')
async def catalog_get_list_legacy():
    products = _read_catalog()
    return {"success": True, "products": products}


@router.post('/api/catalog/get_entry')
async def catalog_get_entry_legacy(data: dict):
    pid = data.get('product_id')
    if pid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "product_id required"})
    items = _read_catalog()
    entry = next((p for p in items if p.get('id') == pid), None)
    if not entry:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})
    return {"success": True, "product": entry}


@router.post('/api/catalog/add')
async def catalog_add_legacy(payload: dict):
    name = payload.get('name')
    if not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "name required"})
    items = _read_catalog()
    new_id = _next_product_id(items)
    
    entry = {
        'id': new_id,
        'name': name,
        'category': payload.get('category', ''),
        'available_stock': payload.get('available_stock', 0),
        'unit': payload.get('unit', 'шт'),
        'retail_price': payload.get('retail_price', 0),
        'created_at': None,
        'updated_at': None,
    }
    items.append(entry)
    _write_catalog(items)
    return {"success": True, "product": entry, "product_id": new_id}


@router.post('/api/catalog/edit')
async def catalog_edit_legacy(payload: dict):
    pid = payload.get('id')
    name = payload.get('name')
    if pid is None or not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "id and name required"})
    items = _read_catalog()
    for i, p in enumerate(items):
        if p.get('id') == pid:
            items[i] = {
                'id': pid,
                'name': name,
                'category': payload.get('category', p.get('category', '')),
                'available_stock': payload.get('available_stock', p.get('available_stock', 0)),
                'unit': payload.get('unit', p.get('unit', 'шт')),
                'retail_price': payload.get('retail_price', p.get('retail_price', 0)),
                'created_at': p.get('created_at'),
                'updated_at': None,
            }
            _write_catalog(items)
            return {"success": True, "product": items[i]}
    return JSONResponse(status_code=404, content={"success": False, "error": "not found"})


@router.post('/api/catalog/delete')
async def catalog_delete_legacy(payload: dict):
    pid = payload.get('product_id')
    if pid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "product_id required"})
    items = _read_catalog()
    new_items = [p for p in items if p.get('id') != pid]
    _write_catalog(new_items)
    return {"success": True}


# ======================
# Warehouse operations storage
# ======================

def _read_warehouse() -> list:
    try:
        if os.path.exists(WAREHOUSE_STORAGE_PATH):
            with open(WAREHOUSE_STORAGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def _write_warehouse(items: list) -> None:
    try:
        with open(WAREHOUSE_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _next_operation_id(items: list) -> int:
    return (max([o.get('id', 0) for o in items] + [0]) + 1)

def _enrich_warehouse_operation(operation: dict) -> dict:
    """Обогащает операцию данными из связанных сущностей"""
    enriched = operation.copy()
    
    # Получаем имя ответственного из базы пользователей
    responsible_id = operation.get('responsible_id')
    if responsible_id:
        try:
            from ...core.database import db_manager
            try:
                responsible_id_int = int(responsible_id) if isinstance(responsible_id, str) else responsible_id
            except (ValueError, TypeError):
                responsible_id_int = None
            
            if responsible_id_int:
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT username, full_name FROM users WHERE id = ?", (responsible_id_int,))
                row = cursor.fetchone()
                if row:
                    enriched['responsible_name'] = row[1] or row[0] or 'Неизвестный'
                else:
                    enriched['responsible_name'] = operation.get('responsible_name', '')
            else:
                enriched['responsible_name'] = operation.get('responsible_name', '')
        except Exception:
            enriched['responsible_name'] = operation.get('responsible_name', '')
    else:
        enriched['responsible_name'] = ''
    
    return enriched


# ======================
# Calculations history (simple storage)
# ======================

def _read_calculations() -> list:
    try:
        if os.path.exists(CALCULATIONS_STORAGE_PATH):
            with open(CALCULATIONS_STORAGE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def _write_calculations(items: list) -> None:
    try:
        with open(CALCULATIONS_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _next_calc_id(items: list) -> int:
    return (max([c.get('id', 0) for c in items] + [0]) + 1)


@router.get('/api/calculations/list')
async def calculations_list_legacy():
    items = _read_calculations()
    # Возвращаем краткий список
    brief = [
        {
            'id': it.get('id'),
            'name': it.get('name') or it.get('Название изделия') or '',
            'created_at': it.get('created_at'),
            'items_count': len(it.get('items') or []),
            'total': it.get('totals') or {}
        } for it in items
    ]
    return {'success': True, 'items': brief}


@router.get('/api/calculations/{calc_id}')
async def calculations_get_entry_legacy(calc_id: int):
    items = _read_calculations()
    for it in items:
        if int(it.get('id', -1)) == int(calc_id):
            return {'success': True, 'calculation': it}
    return JSONResponse(status_code=404, content={'success': False, 'error': 'not found'})


@router.post('/api/calculations/save')
async def calculations_save_legacy(payload: dict):
    """
    Ожидаемый формат payload:
    {
      id?: number,            # если есть — обновляем, иначе создаём
      name: string,           # Название изделия (общее)
      items: [                # Позиции изделия (сортаменты/заготовки)
        { ... позиция ... }
      ],
      totals?: { ... },
      meta?: { ... }
    }
    """
    items = _read_calculations()
    from datetime import datetime
    now_iso = datetime.utcnow().isoformat()

    calc_id = payload.get('id')
    if calc_id is None:
        new_id = _next_calc_id(items)
        entry = {
            'id': new_id,
            'name': payload.get('name') or payload.get('Название изделия') or '',
            'items': payload.get('items') or [],
            'totals': payload.get('totals') or {},
            'meta': payload.get('meta') or {},
            'created_at': now_iso,
            'updated_at': now_iso,
        }
        items.append(entry)
        _write_calculations(items)
        return {'success': True, 'id': new_id}
    else:
        # update
        for i, it in enumerate(items):
            if int(it.get('id', -1)) == int(calc_id):
                items[i] = {
                    'id': int(calc_id),
                    'name': payload.get('name') or payload.get('Название изделия') or it.get('name') or '',
                    'items': payload.get('items') if 'items' in payload else it.get('items', []),
                    'totals': payload.get('totals') if 'totals' in payload else it.get('totals', {}),
                    'meta': payload.get('meta') if 'meta' in payload else it.get('meta', {}),
                    'created_at': it.get('created_at'),
                    'updated_at': now_iso,
                }
                _write_calculations(items)
                return {'success': True, 'id': int(calc_id)}
        return JSONResponse(status_code=404, content={'success': False, 'error': 'not found'})


@router.post('/api/calculations/delete')
async def calculations_delete_legacy(payload: dict):
    calc_id = payload.get('id')
    if calc_id is None:
        return JSONResponse(status_code=400, content={'success': False, 'error': 'id required'})
    items = _read_calculations()
    new_items = [it for it in items if int(it.get('id', -1)) != int(calc_id)]
    _write_calculations(new_items)
    return {'success': True}


# ======================
# Materials settings (prices_metal_materials.json)
# ======================

def _read_materials_settings() -> list:
    """
    Читает настройки материалов.
    Поддерживает как старую структуру (плоский массив), так и новую (группировка по категориям).
    Всегда возвращает плоский массив для обратной совместимости.
    """
    try:
        if os.path.exists(MATERIALS_SETTINGS_PATH):
            with open(MATERIALS_SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Новая структура: группировка по категориям
                materials_dict = data.get('prices_metal_materials')
                if isinstance(materials_dict, dict):
                    # Преобразуем словарь категорий в плоский массив
                    result = []
                    for category, materials_list in materials_dict.items():
                        for material in materials_list:
                            result.append({
                                'id': material.get('id'),
                                'category': category,
                                'grade': material.get('grade', ''),
                                'density': material.get('density', 0),
                                'price': material.get('price', 0),
                            })
                    return result
                
                # Старая структура: плоский массив
                if isinstance(materials_dict, list):
                    return materials_dict
                
                # Прямой массив (legacy)
                if isinstance(data, list):
                    return data
    except Exception:
        pass
    return []

def _write_materials_settings(items: list) -> None:
    """
    Записывает настройки материалов в оптимизированном формате (группировка по категориям).
    """
    try:
        # Группируем по категориям для оптимизации
        grouped = {}
        for material in items:
            category = material.get('category', '')
            if category:
                if category not in grouped:
                    grouped[category] = []
                
                # Создаем элемент без поля category
                material_item = {
                    'id': material.get('id'),
                    'grade': material.get('grade', ''),
                    'density': material.get('density', 0),
                    'price': material.get('price', 0),
                }
                grouped[category].append(material_item)
        
        # Сортируем материалы внутри каждой категории по ID
        for category in grouped:
            grouped[category].sort(key=lambda x: x.get('id', 0))
        
        # Сохраняем в оптимизированном формате
        with open(MATERIALS_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump({ 'prices_metal_materials': dict(sorted(grouped.items())) }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _next_material_id(items: list) -> int:
    return (max([m.get('id', 0) for m in items] + [0]) + 1)


@router.get('/api/materials/settings')
async def materials_settings_list():
    return { 'success': True, 'items': _read_materials_settings() }


@router.post('/api/materials/add')
async def materials_add(payload: dict):
    required = ['category', 'grade']
    for k in required:
        if not payload.get(k):
            return JSONResponse(status_code=400, content={'success': False, 'error': f'{k} required'})
    items = _read_materials_settings()
    new_id = _next_material_id(items)
    entry = {
        'id': new_id,
        'category': payload.get('category', ''),
        'grade': payload.get('grade', ''),
        'density': payload.get('density', 0),
        'price': payload.get('price', 0),
    }
    items.append(entry)
    _write_materials_settings(items)
    return { 'success': True, 'material': entry, 'id': new_id }


@router.post('/api/materials/edit')
async def materials_edit(payload: dict):
    mid = payload.get('id')
    if mid is None:
        return JSONResponse(status_code=400, content={'success': False, 'error': 'id required'})
    items = _read_materials_settings()
    for i, m in enumerate(items):
        if int(m.get('id', -1)) == int(mid):
            items[i] = {
                'id': int(mid),
                'category': payload.get('category', m.get('category', '')),
                'grade': payload.get('grade', m.get('grade', '')),
                'density': payload.get('density', m.get('density', 0)),
                'price': payload.get('price', m.get('price', 0)),
            }
            _write_materials_settings(items)
            return { 'success': True }
    return JSONResponse(status_code=404, content={'success': False, 'error': 'not found'})


@router.post('/api/materials/delete')
async def materials_delete(payload: dict):
    mid = payload.get('id')
    if mid is None:
        return JSONResponse(status_code=400, content={'success': False, 'error': 'id required'})
    items = _read_materials_settings()
    new_items = [m for m in items if int(m.get('id', -1)) != int(mid)]
    _write_materials_settings(new_items)
    return { 'success': True }


@router.get('/api/warehouse/get_list')
async def warehouse_get_list_legacy(request: Request):
    type_filter = request.query_params.get('type', '')
    operations = _read_warehouse()
    
    # Фильтруем по типу операции
    if type_filter:
        operations = [o for o in operations if o.get('operation_type') == type_filter]
    
    # Обогащаем каждую операцию данными из связанных сущностей
    enriched_operations = [_enrich_warehouse_operation(o) for o in operations]
    return {"success": True, "operations": enriched_operations}


@router.post('/api/warehouse/add')
async def warehouse_add_legacy(payload: dict):
    name = payload.get('name')
    if not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "name required"})
    items = _read_warehouse()
    new_id = _next_operation_id(items)
    
    entry = {
        'id': new_id,
        'name': name,
        'operation_type': payload.get('type', 'income'),
        'type': payload.get('type', ''),
        'status': payload.get('status', 'Черновик'),
        'date': payload.get('date', ''),
        'supplier': payload.get('supplier', ''),
        'responsible_id': payload.get('responsible_id') or None,
        'amount': payload.get('amount', 0),
        'warehouse': payload.get('warehouse', ''),
        'warehouses': payload.get('warehouses', []),
        'client': payload.get('client', ''),
        'from_warehouse': payload.get('from_warehouse', ''),
        'to_warehouse': payload.get('to_warehouse', ''),
        'created_at': None,
        'updated_at': None,
    }
    items.append(entry)
    _write_warehouse(items)
    
    # Возвращаем обогащенную операцию
    enriched_entry = _enrich_warehouse_operation(entry)
    return {"success": True, "operation": enriched_entry, "operation_id": new_id}


@router.post('/api/warehouse/edit')
async def warehouse_edit_legacy(payload: dict):
    oid = payload.get('id')
    name = payload.get('name')
    if oid is None or not name:
        return JSONResponse(status_code=400, content={"success": False, "error": "id and name required"})
    items = _read_warehouse()
    for i, o in enumerate(items):
        if o.get('id') == oid:
            # Сохраняем существующие значения для полей, которые не переданы
            items[i] = {
                'id': oid,
                'name': name,
                'operation_type': payload.get('type', o.get('operation_type', 'income')),
                'type': payload.get('type', o.get('type', '')),
                'status': payload.get('status', o.get('status', 'Черновик')),
                'date': payload.get('date', o.get('date', '')),
                'supplier': payload.get('supplier', o.get('supplier', '')),
                'responsible_id': payload.get('responsible_id') if 'responsible_id' in payload else o.get('responsible_id'),
                'amount': payload.get('amount', o.get('amount', 0)),
                'warehouse': payload.get('warehouse', o.get('warehouse', '')),
                'warehouses': payload.get('warehouses', o.get('warehouses', [])),
                'client': payload.get('client', o.get('client', '')),
                'from_warehouse': payload.get('from_warehouse', o.get('from_warehouse', '')),
                'to_warehouse': payload.get('to_warehouse', o.get('to_warehouse', '')),
                'created_at': o.get('created_at'),
                'updated_at': None,
            }
            _write_warehouse(items)
            
            # Возвращаем обогащенную операцию
            enriched_entry = _enrich_warehouse_operation(items[i])
            return {"success": True, "operation": enriched_entry}
    return JSONResponse(status_code=404, content={"success": False, "error": "not found"})


@router.post('/api/warehouse/delete')
async def warehouse_delete_legacy(payload: dict):
    oid = payload.get('operation_id')
    if oid is None:
        return JSONResponse(status_code=400, content={"success": False, "error": "operation_id required"})
    items = _read_warehouse()
    new_items = [o for o in items if o.get('id') != oid]
    _write_warehouse(new_items)
    return {"success": True}
