#!/usr/bin/env python3
"""
Тест проверки пароля
"""
import sqlite3
import bcrypt

def test_password():
    print("🔐 Тест проверки пароля...")
    
    # Подключаемся к БД
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Получаем пользователя admin
    cursor.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    user = cursor.fetchone()
    
    if not user:
        print("❌ Пользователь admin не найден")
        return
    
    print(f"✅ Пользователь admin найден")
    print(f"   Password Hash: {user['password_hash']}")
    
    # Тестируем пароль 'admin'
    password = 'admin'
    stored_hash = user['password_hash']
    
    print(f"\n🔍 Тестируем пароль: '{password}'")
    print(f"   Stored Hash: {stored_hash}")
    
    try:
        # Проверяем пароль
        is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        print(f"✅ Результат проверки: {is_valid}")
        
        if is_valid:
            print("🎉 Пароль правильный!")
        else:
            print("❌ Пароль неправильный!")
            
            # Попробуем создать новый хеш
            print("\n🔄 Создаем новый хеш для 'admin'...")
            new_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
            print(f"   Новый хеш: {new_hash.decode('utf-8')}")
            
            # Проверяем новый хеш
            is_new_valid = bcrypt.checkpw('admin'.encode('utf-8'), new_hash)
            print(f"   Новый хеш работает: {is_new_valid}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки пароля: {e}")
    
    conn.close()

if __name__ == "__main__":
    test_password()

