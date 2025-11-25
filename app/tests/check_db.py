#!/usr/bin/env python3
"""
Проверка базы данных
"""
import sqlite3
import os

def check_database():
    print("🔍 Проверка базы данных...")
    
    db_path = "users.db"
    if not os.path.exists(db_path):
        print(f"❌ Файл {db_path} не найден")
        return
    
    print(f"✅ Файл {db_path} найден")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Таблицы в БД: {[table[0] for table in tables]}")
        
        # Проверяем пользователей
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        print(f"👥 Пользователи в БД: {len(users)}")
        
        for user in users:
            print(f"   - {user['username']} ({user['email']}) - Admin: {user['is_admin']}")
            print(f"     Password Hash: {user['password_hash'][:30]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")

if __name__ == "__main__":
    check_database()

