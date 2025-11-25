"""
Скрипт для запуска всех миграций CRM системы
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))


def run_migrations():
    """Запускает все миграции по порядку"""
    print("=" * 60)
    print("Запуск миграций CRM системы")
    print("=" * 60)
    
    # 1. Миграция customers.json
    print("\n[1/4] Миграция customers.json...")
    try:
        from app.scripts.migrate_customers import migrate_customers
        if migrate_customers():
            print("✅ Миграция customers.json завершена успешно")
        else:
            print("❌ Ошибка при миграции customers.json")
            return False
    except Exception as e:
        print(f"❌ Ошибка при миграции customers.json: {e}")
        return False
    
    # 2. Миграция contacts.json
    print("\n[2/4] Миграция contacts.json...")
    try:
        from app.scripts.migrate_contacts import migrate_contacts
        if migrate_contacts():
            print("✅ Миграция contacts.json завершена успешно")
        else:
            print("❌ Ошибка при миграции contacts.json")
            return False
    except Exception as e:
        print(f"❌ Ошибка при миграции contacts.json: {e}")
        return False
    
    # 3. Инициализация воронки по умолчанию
    print("\n[3/4] Инициализация воронки по умолчанию...")
    try:
        from app.scripts.init_default_funnel import init_default_funnel
        if init_default_funnel():
            print("✅ Воронка по умолчанию создана успешно")
        else:
            print("❌ Ошибка при создании воронки по умолчанию")
            return False
    except Exception as e:
        print(f"❌ Ошибка при создании воронки по умолчанию: {e}")
        return False
    
    # 4. Миграция proposals → deals (опционально)
    print("\n[4/4] Миграция proposals → deals...")
    response = input("Выполнить миграцию proposals в deals? (y/n): ").strip().lower()
    if response == 'y':
        try:
            from app.scripts.migrate_proposals_to_deals import migrate_proposals_to_deals
            if migrate_proposals_to_deals():
                print("✅ Миграция proposals → deals завершена успешно")
            else:
                print("⚠️  Миграция proposals → deals завершилась с предупреждениями")
        except Exception as e:
            print(f"⚠️  Ошибка при миграции proposals → deals: {e}")
            print("Продолжаем...")
    else:
        print("⏭️  Миграция proposals → deals пропущена")
    
    print("\n" + "=" * 60)
    print("✅ Все миграции завершены!")
    print("=" * 60)
    print("\nСледующие шаги:")
    print("1. Запустите сервер: python run_new.py")
    print("2. Проверьте API документацию: http://localhost:8000/docs")
    print("3. Протестируйте новые endpoints:")
    print("   - GET /api/v1/customers")
    print("   - GET /api/v1/contacts")
    print("   - GET /api/v1/deals")
    print("   - GET /api/v1/funnels")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)



