#!/usr/bin/env python3
"""
Обновление существующих записей с пустыми статусом и приоритетом
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db_manager

def update_empty_status_priority():
    print("🔧 Обновляем записи с пустыми статусом и приоритетом...")
    
    try:
        with db_manager.get_connection() as conn:
            # Обновляем все записи, у которых status или priority не пустые
            # но мы хотим их сделать пустыми для новых записей
            conn.execute("""
                UPDATE proposals 
                SET status = '', priority = '' 
                WHERE status = 'draft' AND priority = 'medium'
            """)
            
            conn.commit()
            
            # Проверяем результат
            cursor = conn.execute("SELECT id, company, status, priority FROM proposals")
            rows = cursor.fetchall()
            
            print(f"📊 Обновлено записей:")
            for row in rows:
                print(f"   ID: {row[0]}, Company: {row[1]}, Status: '{row[2]}', Priority: '{row[3]}'")
            
        print("✅ Записи обновлены!")
        
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_empty_status_priority()
