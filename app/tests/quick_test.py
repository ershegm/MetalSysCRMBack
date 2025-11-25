#!/usr/bin/env python3
"""
Быстрый тест для проверки входа
"""
import urllib.request
import urllib.parse
import json

def test_login():
    print("🔐 Тестируем вход в систему...")
    
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
            print(f"Ответ: {data}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Legacy login ошибка: {e.code} - {e.reason}")
        print(f"Ответ: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    if success:
        print("\n🎉 Вход в систему работает!")
    else:
        print("\n❌ Проблема с входом в систему")

