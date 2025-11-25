#!/usr/bin/env python3
"""
Исправление пароля admin
"""
import sqlite3
import bcrypt

def fix_password():
    print("🔧 Исправление пароля admin...")
    
    # Подключаемся к БД
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Создаем правильный хеш для пароля 'admin'
    password = 'admin'
    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    new_hash_str = new_hash.decode('utf-8')
    
    print(f"🔐 Создаем новый хеш для пароля '{password}'")
    print(f"   Новый хеш: {new_hash_str}")
    
    # Проверяем, что новый хеш работает
    is_valid = bcrypt.checkpw(password.encode('utf-8'), new_hash)
    print(f"✅ Новый хеш работает: {is_valid}")
    
    if is_valid:
        # Обновляем пароль в базе данных
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (new_hash_str, 'admin')
        )
        conn.commit()
        
        print("✅ Пароль admin обновлен в базе данных")
        
        # Проверяем обновление
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", ('admin',))
        updated_user = cursor.fetchone()
        
        if updated_user:
            print(f"✅ Проверяем обновленный хеш: {updated_user['password_hash'][:30]}...")
            
            # Финальная проверка
            final_check = bcrypt.checkpw(password.encode('utf-8'), updated_user['password_hash'].encode('utf-8'))
            print(f"🎉 Финальная проверка: {final_check}")
            
            if final_check:
                print("🎊 Пароль admin исправлен и работает!")
            else:
                print("❌ Что-то пошло не так")
        else:
            print("❌ Пользователь не найден после обновления")
    else:
        print("❌ Новый хеш не работает")
    
    conn.close()

if __name__ == "__main__":
    fix_password()

