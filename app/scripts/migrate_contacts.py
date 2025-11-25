"""
Скрипт миграции contacts.json - расширение структуры
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


def migrate_contacts():
    """Мигрирует contacts.json - расширяет структуру для новой схемы"""
    contacts_path = os.path.join(os.path.dirname(__file__), '..', 'contacts.json')
    
    # Создаём бэкап
    backup_path = contacts_path + '.backup'
    if os.path.exists(contacts_path):
        import shutil
        shutil.copy2(contacts_path, backup_path)
        print(f"Создан бэкап: {backup_path}")
    
    # Читаем текущие данные
    contacts = read_json_file(contacts_path)
    
    print(f"Найдено контактов: {len(contacts)}")
    
    # Мигрируем каждую запись
    migrated_count = 0
    for contact in contacts:
        migrated = False
        
        # Добавляем external_id если нет
        if 'external_id' not in contact or not contact['external_id']:
            contact['external_id'] = generate_external_id('contact', contact.get('id', 0))
            migrated = True
        
        # Разбиваем name на first_name, last_name
        name = contact.get('name', '').strip()
        if name and ('first_name' not in contact or not contact.get('first_name')):
            parts = name.split()
            if len(parts) >= 2:
                contact['last_name'] = parts[0]
                contact['first_name'] = parts[1]
                contact['middle_name'] = ' '.join(parts[2:]) if len(parts) > 2 else ''
            elif len(parts) == 1:
                contact['first_name'] = parts[0]
                contact['last_name'] = ''
                contact['middle_name'] = ''
            else:
                contact['first_name'] = ''
                contact['last_name'] = ''
                contact['middle_name'] = ''
            migrated = True
        
        # Инициализируем поля если нет
        for field in ['first_name', 'last_name', 'middle_name']:
            if field not in contact:
                contact[field] = ''
        
        # Обеспечиваем наличие name для обратной совместимости
        if 'name' not in contact or not contact['name']:
            first = contact.get('first_name', '')
            last = contact.get('last_name', '')
            contact['name'] = f"{first} {last}".strip() if first or last else ''
        
        # Нормализуем responsible_id/responsible_user_id
        responsible_id = contact.get('responsible_id') or contact.get('responsible_user_id')
        if responsible_id:
            contact['responsible_id'] = responsible_id  # Legacy
            contact['responsible_user_id'] = responsible_id  # Новое
        else:
            contact['responsible_id'] = None
            contact['responsible_user_id'] = None
        
        # Создаём массив communications из legacy полей email/phone
        if 'communications' not in contact or not contact['communications']:
            communications = []
            email = contact.get('email', '').strip()
            phone = contact.get('phone', '').strip()
            
            if email:
                communications.append({
                    'id': len(communications) + 1,
                    'comm_type': 'EMAIL',
                    'value_type': 'WORK',
                    'value': email,
                    'is_primary': True,
                })
            
            if phone:
                communications.append({
                    'id': len(communications) + 1,
                    'comm_type': 'PHONE',
                    'value_type': 'WORK',
                    'value': phone,
                    'is_primary': True,
                })
            
            contact['communications'] = communications
            migrated = True
        
        # Инициализируем массив tags если нет
        if 'tags' not in contact:
            contact['tags'] = contact.get('tags', [])  # Может быть уже в данных
            if not isinstance(contact['tags'], list):
                contact['tags'] = []
            migrated = True
        
        # Инициализируем обязательные поля
        for field in ['position', 'department', 'email', 'phone']:
            if field not in contact:
                contact[field] = ''
        
        if 'deals_count' not in contact:
            contact['deals_count'] = 0
            migrated = True
        
        if 'is_active' not in contact:
            contact['is_active'] = True
            migrated = True
        
        if 'created_at' not in contact or not contact['created_at']:
            contact['created_at'] = datetime.utcnow().isoformat()
            migrated = True
        
        if 'updated_at' not in contact:
            contact['updated_at'] = datetime.utcnow().isoformat()
            migrated = True
        
        if migrated:
            migrated_count += 1
    
    # Сохраняем мигрированные данные
    if write_json_file(contacts_path, contacts):
        print(f"Миграция завершена. Обновлено записей: {migrated_count}")
        print(f"Сохранено в: {contacts_path}")
    else:
        print("Ошибка при сохранении мигрированных данных")
        return False
    
    return True


if __name__ == "__main__":
    print("Начало миграции contacts.json...")
    success = migrate_contacts()
    if success:
        print("Миграция успешно завершена!")
        sys.exit(0)
    else:
        print("Миграция завершилась с ошибками!")
        sys.exit(1)




