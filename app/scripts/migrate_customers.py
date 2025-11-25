"""
Скрипт миграции customers.json - расширение структуры
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Добавляем корневую директорию проекта в путь
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.utils.storage import read_json_file, write_json_file, generate_external_id
from app.utils.enums import CUSTOMER_TYPE_MAPPING


def migrate_customers():
    """Мигрирует customers.json - расширяет структуру для новой схемы"""
    customers_path = os.path.join(os.path.dirname(__file__), '..', 'customers.json')
    
    # Создаём бэкап
    backup_path = customers_path + '.backup'
    if os.path.exists(customers_path):
        import shutil
        shutil.copy2(customers_path, backup_path)
        print(f"Создан бэкап: {backup_path}")
    
    # Читаем текущие данные
    customers = read_json_file(customers_path)
    
    print(f"Найдено клиентов: {len(customers)}")
    
    # Мигрируем каждую запись
    migrated_count = 0
    for customer in customers:
        migrated = False
        
        # Добавляем external_id если нет
        if 'external_id' not in customer or not customer['external_id']:
            customer['external_id'] = generate_external_id('customer', customer.get('id', 0))
            migrated = True
        
        # Нормализуем customer_type (из type)
        customer_type = customer.get('customer_type')
        if not customer_type:
            legacy_type = customer.get('type', 3)
            # Преобразуем в новый формат
            if isinstance(legacy_type, int):
                customer['customer_type'] = legacy_type
            elif isinstance(legacy_type, str) and legacy_type.isdigit():
                customer['customer_type'] = int(legacy_type)
            else:
                customer['customer_type'] = 3
            migrated = True
        
        # Обеспечиваем наличие type для обратной совместимости
        if 'type' not in customer:
            customer['type'] = customer['customer_type']
        
        # Создаём массив contacts из legacy полей email/phone
        if 'contacts' not in customer or not customer['contacts']:
            contacts = []
            email = customer.get('email', '').strip()
            phone = customer.get('phone', '').strip()
            
            if email:
                contacts.append({
                    'id': len(contacts) + 1,
                    'contact_type': 'EMAIL',
                    'value_type': 'WORK',
                    'value': email,
                    'is_primary': True,
                })
            
            if phone:
                contacts.append({
                    'id': len(contacts) + 1,
                    'contact_type': 'PHONE',
                    'value_type': 'WORK',
                    'value': phone,
                    'is_primary': True,
                })
            
            customer['contacts'] = contacts
            migrated = True
        
        # Инициализируем массив files если нет
        if 'files' not in customer:
            customer['files'] = []
            migrated = True
        
        # Добавляем новые поля если нет
        if 'is_active' not in customer:
            customer['is_active'] = True
            migrated = True
        
        if 'created_at' not in customer or not customer['created_at']:
            customer['created_at'] = datetime.utcnow().isoformat()
            migrated = True
        
        if 'updated_at' not in customer:
            customer['updated_at'] = datetime.utcnow().isoformat()
            migrated = True
        
        if 'currency_id' not in customer:
            customer['currency_id'] = 'RUB'
            migrated = True
        
        # Обеспечиваем наличие всех обязательных полей
        for field in ['name', 'email', 'phone', 'address_legal', 'address_real', 'inn', 'kpp', 'ogrn', 'agreement', 'manager_name', 'manager_post', 'notes']:
            if field not in customer:
                customer[field] = ''
        
        if migrated:
            migrated_count += 1
    
    # Сохраняем мигрированные данные
    if write_json_file(customers_path, customers):
        print(f"Миграция завершена. Обновлено записей: {migrated_count}")
        print(f"Сохранено в: {customers_path}")
    else:
        print("Ошибка при сохранении мигрированных данных")
        return False
    
    return True


if __name__ == "__main__":
    print("Начало миграции customers.json...")
    success = migrate_customers()
    if success:
        print("Миграция успешно завершена!")
        sys.exit(0)
    else:
        print("Миграция завершилась с ошибками!")
        sys.exit(1)




