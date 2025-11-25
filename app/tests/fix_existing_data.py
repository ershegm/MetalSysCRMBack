#!/usr/bin/env python3
"""
Исправление существующих данных в базе
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db_manager

def fix_existing_data():
    print("🔧 Исправляем существующие данные...")
    
    try:
        with db_manager.get_connection() as conn:
            # Обновляем все записи, у которых нет status или priority
            conn.execute("""
                UPDATE proposals 
                SET status = 'draft', priority = 'medium' 
                WHERE status IS NULL OR status = '' OR priority IS NULL OR priority = ''
            """)
            
            # Устанавливаем company для записей, где его нет
            conn.execute("""
                UPDATE proposals 
                SET company = 'Тестовая компания' 
                WHERE company IS NULL OR company = ''
            """)
            
            conn.commit()
            
            # Проверяем результат
            cursor = conn.execute("SELECT id, company, status, priority FROM proposals")
            rows = cursor.fetchall()
            
            print(f"📊 Обновлено {len(rows)} записей:")
            for row in rows:
                print(f"   ID: {row[0]}, Company: {row[1]}, Status: {row[2]}, Priority: {row[3]}")
            
        print("✅ Данные исправлены!")
        
    except Exception as e:
        print(f"❌ Ошибка исправления: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_existing_data()
