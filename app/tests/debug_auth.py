#!/usr/bin/env python3
"""
Отладка аутентификации
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db_manager
from app.core.security import SecurityManager
import bcrypt

def debug_auth():
    print("🔍 Отладка аутентификации...")
    
    # 1. Проверяем базу данных
    print("\n1. Проверяем базу данных...")
    try:
        db_manager.init_database()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return
    
    # 2. Проверяем пользователя admin
    print("\n2. Проверяем пользователя admin...")
    try:
        user = db_manager.get_user_by_username('admin')
        if user:
            print(f"✅ Пользователь admin найден:")
            print(f"   ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            print(f"   Is Admin: {user['is_admin']}")
            print(f"   Password Hash: {user['password_hash'][:20]}...")
        else:
            print("❌ Пользователь admin не найден")
            return
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return
    
    # 3. Проверяем хеширование пароля
    print("\n3. Проверяем хеширование пароля...")
    try:
        security_manager = SecurityManager()
        
        # Проверяем пароль 'admin'
        is_valid = security_manager.verify_password('admin', user['password_hash'])
        print(f"✅ Проверка пароля 'admin': {is_valid}")
        
        # Проверяем неправильный пароль
        is_invalid = security_manager.verify_password('wrong', user['password_hash'])
        print(f"✅ Проверка неправильного пароля: {is_invalid}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки пароля: {e}")
        return
    
    # 4. Тестируем полную аутентификацию
    print("\n4. Тестируем полную аутентификацию...")
    try:
        auth_result = security_manager.authenticate_user('admin', 'admin')
        if auth_result:
            print(f"✅ Аутентификация успешна: {auth_result['username']}")
        else:
            print("❌ Аутентификация не удалась")
    except Exception as e:
        print(f"❌ Ошибка аутентификации: {e}")
        return
    
    # 5. Проверяем создание нового хеша
    print("\n5. Проверяем создание нового хеша...")
    try:
        new_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
        print(f"✅ Новый хеш создан: {new_hash.decode('utf-8')[:20]}...")
        
        # Проверяем новый хеш
        is_new_valid = bcrypt.checkpw('admin'.encode('utf-8'), new_hash)
        print(f"✅ Новый хеш работает: {is_new_valid}")
        
    except Exception as e:
        print(f"❌ Ошибка создания хеша: {e}")
        return
    
    print("\n🎉 Отладка завершена!")

if __name__ == "__main__":
    debug_auth()

