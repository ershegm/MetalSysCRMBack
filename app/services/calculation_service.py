"""
Сервис расчетов
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..core.exceptions import NotFoundError
from ..models.calculation import CalculationCreate, CalculationUpdate, CalculationResponse


# Путь к файлу с расчетами
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CALCULATIONS_STORAGE_PATH = os.path.join(ROOT_DIR, 'calculations.json')


def _read_calculations() -> list:
    """Чтение расчетов из JSON файла"""
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
    """Запись расчетов в JSON файл"""
    try:
        with open(CALCULATIONS_STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise Exception(f"Ошибка записи расчетов: {str(e)}")


def _next_calc_id(items: list) -> int:
    """Получение следующего ID для расчета"""
    return (max([c.get('id', 0) for c in items] + [0]) + 1)


def _convert_to_dict(calculation: CalculationCreate) -> Dict[str, Any]:
    """Конвертация Pydantic модели в словарь для сохранения"""
    return {
        'name': calculation.name,
        'assortments': [item.model_dump(by_alias=True) for item in calculation.assortments],
        'blanks': [item.model_dump() for item in calculation.blanks],
        'global_operations': [item.model_dump(by_alias=True) for item in calculation.global_operations],
        'global_markup': calculation.global_markup,
        'global_markup_apply_to_assortments': calculation.global_markup_apply_to_assortments,
        'global_markup_apply_to_blanks': calculation.global_markup_apply_to_blanks,
        'global_markup_apply_to_operations': calculation.global_markup_apply_to_operations,
    }


def _convert_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Конвертация данных из JSON в формат для ответа"""
    # Возвращаем данные как есть, так как они уже сохранены с alias (camelCase)
    return {
        'id': data.get('id'),
        'name': data.get('name', ''),
        'assortments': data.get('assortments', []),
        'blanks': data.get('blanks', []),
        'global_operations': data.get('global_operations', []),
        'global_markup': data.get('global_markup', 0.0),
        'global_markup_apply_to_assortments': data.get('global_markup_apply_to_assortments', True),
        'global_markup_apply_to_blanks': data.get('global_markup_apply_to_blanks', False),
        'global_markup_apply_to_operations': data.get('global_markup_apply_to_operations', False),
        'created_at': data.get('created_at'),
        'updated_at': data.get('updated_at'),
    }


class CalculationService:
    """Сервис управления расчетами"""
    
    async def get_calculations(self) -> List[Dict[str, Any]]:
        """Получение списка расчетов (краткая информация)"""
        items = _read_calculations()
        brief = []
        for it in items:
            # Поддержка старого формата (legacy)
            if 'items' in it:
                # Старый формат - конвертируем
                items_count = len(it.get('items', []))
                # Для старого формата используем базовые значения
                cost_price = sum([item.get('materialCost', 0) for item in it.get('items', [])])
                markup_value = 0
                markup_percent = 0
                total_price = cost_price
            else:
                # Новый формат
                assortments = it.get('assortments', [])
                blanks = it.get('blanks', [])
                global_ops = it.get('global_operations', [])
                global_markup = it.get('global_markup', 0.0)
                
                items_count = len(assortments) + len(blanks)
                
                # Расчет себестоимости
                assortments_material_cost = sum([a.get('materialCost', 0) for a in assortments])
                assortments_processing_cost = sum([a.get('processingCost', 0) for a in assortments])
                # Для заготовок: базовая стоимость = price * quantity (без наценки)
                blanks_cost = sum([b.get('price', 0) * b.get('quantity', 0) for b in blanks])
                # Для глобальных операций: используем сохраненную стоимость или рассчитываем из операций
                global_ops_cost = sum([
                    op.get('cost', 0) or 0  # Используем сохраненную стоимость операции
                    for op in global_ops
                ])
                cost_price = assortments_material_cost + assortments_processing_cost + blanks_cost + global_ops_cost
                
                # Расчет наценки
                assortments_markup = sum([
                    (a.get('materialCost', 0) + a.get('processingCost', 0)) * (a.get('markup', 0) / 100)
                    for a in assortments
                ])
                # Наценка на заготовки: sum - базовая стоимость
                blanks_markup = sum([
                    b.get('sum', 0) - (b.get('price', 0) * b.get('quantity', 0))
                    for b in blanks
                ])
                markup_value = assortments_markup + blanks_markup
                
                # Цена без глобальной наценки (себестоимость + наценки)
                price_without_global = cost_price + markup_value
                
                # Получаем настройки применения глобальной наценки
                apply_to_assortments = it.get('global_markup_apply_to_assortments', True)
                apply_to_blanks = it.get('global_markup_apply_to_blanks', False)
                apply_to_operations = it.get('global_markup_apply_to_operations', False)
                
                # Расчет базы для глобальной наценки (только к выбранным категориям)
                global_markup_base = 0
                if apply_to_assortments:
                    assortments_total = sum([
                        (a.get('materialCost', 0) + a.get('processingCost', 0)) * (1 + a.get('markup', 0) / 100)
                        for a in assortments
                    ])
                    global_markup_base += assortments_total
                if apply_to_blanks:
                    blanks_total = sum([b.get('sum', 0) for b in blanks])
                    global_markup_base += blanks_total
                if apply_to_operations:
                    # Для операций используем сохраненную стоимость
                    ops_total = sum([op.get('cost', 0) or 0 for op in global_ops])
                    global_markup_base += ops_total
                
                # Если ничего не выбрано, применяем ко всему (для обратной совместимости)
                if not apply_to_assortments and not apply_to_blanks and not apply_to_operations:
                    global_markup_base = price_without_global
                
                # Глобальная наценка
                global_markup_value = global_markup_base * (global_markup / 100)
                # Итоговая цена = цена без глобальной наценки + глобальная наценка
                total_price = price_without_global + global_markup_value
                
                # Процент наценки (относительно себестоимости)
                markup_percent = (markup_value / cost_price * 100) if cost_price > 0 else 0
            
            brief.append({
                'id': it.get('id'),
                'name': it.get('name') or it.get('Название изделия') or '',
                'created_at': it.get('created_at'),
                'items_count': items_count,
                'cost_price': cost_price,
                'markup_percent': markup_percent,
                'markup_value': markup_value,
                'total_price': total_price,
                'total': it.get('totals') or {}
            })
        return brief
    
    async def get_calculation_by_id(self, calculation_id: int) -> Dict[str, Any]:
        """Получение полного расчета по ID"""
        items = _read_calculations()
        for it in items:
            if int(it.get('id', -1)) == int(calculation_id):
                # Поддержка старого формата (legacy)
                if 'items' in it:
                    # Старый формат - возвращаем как есть для обратной совместимости
                    return it
                else:
                    # Новый формат
                    return _convert_from_dict(it)
        raise NotFoundError(f"Расчет с ID {calculation_id} не найден")
    
    async def create_calculation(self, calculation_data: CalculationCreate) -> Dict[str, Any]:
        """Создание нового расчета с валидацией"""
        items = _read_calculations()
        new_id = _next_calc_id(items)
        now_iso = datetime.utcnow().isoformat()
        
        entry = {
            'id': new_id,
            'name': calculation_data.name,
            'assortments': [item.model_dump(by_alias=True, exclude_none=True) for item in calculation_data.assortments],
            'blanks': [item.model_dump(exclude_none=True) for item in calculation_data.blanks],
            'global_operations': [item.model_dump(by_alias=True, exclude_none=True) for item in calculation_data.global_operations],
            'global_markup': calculation_data.global_markup,
            'global_markup_apply_to_assortments': calculation_data.global_markup_apply_to_assortments,
            'global_markup_apply_to_blanks': calculation_data.global_markup_apply_to_blanks,
            'global_markup_apply_to_operations': calculation_data.global_markup_apply_to_operations,
            'created_at': now_iso,
            'updated_at': now_iso,
        }
        
        items.append(entry)
        _write_calculations(items)
        
        return {
            'id': new_id,
            'message': 'Расчет успешно создан'
        }
    
    async def update_calculation(self, calculation_id: int, calculation_data: CalculationUpdate) -> Dict[str, Any]:
        """Обновление расчета с валидацией"""
        items = _read_calculations()
        now_iso = datetime.utcnow().isoformat()
        
        for i, it in enumerate(items):
            if int(it.get('id', -1)) == int(calculation_id):
                # Обновляем только переданные поля
                update_data = {}
                
                if calculation_data.name is not None:
                    update_data['name'] = calculation_data.name
                if calculation_data.assortments is not None:
                    update_data['assortments'] = [item.model_dump(by_alias=True, exclude_none=True) for item in calculation_data.assortments]
                if calculation_data.blanks is not None:
                    update_data['blanks'] = [item.model_dump(exclude_none=True) for item in calculation_data.blanks]
                if calculation_data.global_operations is not None:
                    update_data['global_operations'] = [item.model_dump(by_alias=True, exclude_none=True) for item in calculation_data.global_operations]
                if calculation_data.global_markup is not None:
                    update_data['global_markup'] = calculation_data.global_markup
                if calculation_data.global_markup_apply_to_assortments is not None:
                    update_data['global_markup_apply_to_assortments'] = calculation_data.global_markup_apply_to_assortments
                if calculation_data.global_markup_apply_to_blanks is not None:
                    update_data['global_markup_apply_to_blanks'] = calculation_data.global_markup_apply_to_blanks
                if calculation_data.global_markup_apply_to_operations is not None:
                    update_data['global_markup_apply_to_operations'] = calculation_data.global_markup_apply_to_operations
                
                # Обновляем запись
                items[i] = {
                    'id': int(calculation_id),
                    'name': update_data.get('name', it.get('name', '')),
                    'assortments': update_data.get('assortments', it.get('assortments', [])),
                    'blanks': update_data.get('blanks', it.get('blanks', [])),
                    'global_operations': update_data.get('global_operations', it.get('global_operations', [])),
                    'global_markup': update_data.get('global_markup', it.get('global_markup', 0.0)),
                    'global_markup_apply_to_assortments': update_data.get('global_markup_apply_to_assortments', it.get('global_markup_apply_to_assortments', True)),
                    'global_markup_apply_to_blanks': update_data.get('global_markup_apply_to_blanks', it.get('global_markup_apply_to_blanks', False)),
                    'global_markup_apply_to_operations': update_data.get('global_markup_apply_to_operations', it.get('global_markup_apply_to_operations', False)),
                    'created_at': it.get('created_at'),
                    'updated_at': now_iso,
                }
                
                _write_calculations(items)
                return {
                    'id': int(calculation_id),
                    'message': 'Расчет успешно обновлен'
                }
        
        raise NotFoundError(f"Расчет с ID {calculation_id} не найден")
    
    async def delete_calculation(self, calculation_id: int) -> Dict[str, bool]:
        """Удаление расчета"""
        items = _read_calculations()
        new_items = [it for it in items if int(it.get('id', -1)) != int(calculation_id)]
        
        if len(new_items) == len(items):
            raise NotFoundError(f"Расчет с ID {calculation_id} не найден")
        
        _write_calculations(new_items)
        return {'success': True}

