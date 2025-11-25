#!/usr/bin/env python3
"""
Тест входа после исправления пароля
"""
import urllib.request
import urllib.parse
import json

def test_login():
    print("🔐 Тестируем вход после исправления пароля...")
    
    # Данные для входа
    login_data = {"username": "admin", "password": "admin"}
    json_data = json.dumps(login_data).encode('utf-8')
    
    # Создаем запрос
    req = urllib.request.Request(
        "http://localhost:8000/api/auth/login",
        data=json_data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"✅ Legacy login: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"Ответ: {result}")
            
            if 'access_token' in result:
                print("🎉 Вход в систему успешен!")
                print(f"Токен: {result['access_token'][:30]}...")
                return True
            else:
                print("❌ Токен не получен")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ Legacy login ошибка: {e.code} - {e.reason}")
        error_data = e.read().decode('utf-8')
        print(f"Ответ: {error_data}")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    if success:
        print("\n🎊 Проблема с входом решена!")
    else:
        print("\n❌ Проблема с входом все еще есть")

