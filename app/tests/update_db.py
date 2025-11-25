#!/usr/bin/env python3
"""
Обновление базы данных
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db_manager

def update_database():
    print("🔄 Обновляем базу данных...")
    
    try:
        # Инициализируем базу данных
        db_manager.init_database()
        print("✅ База данных инициализирована")
        
        # Добавляем недостающие колонки
        db_manager.add_missing_columns()
        print("✅ Недостающие колонки добавлены")
        
        # Проверяем структуру таблицы
        with db_manager.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(proposals)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"📋 Колонки в таблице proposals: {columns}")
            
            # Проверяем данные
            cursor = conn.execute("SELECT * FROM proposals LIMIT 1")
            row = cursor.fetchone()
            if row:
                print(f"📊 Пример данных: {dict(row)}")
            else:
                print("📊 Нет данных в таблице")
        
        print("🎉 Обновление завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_database()
