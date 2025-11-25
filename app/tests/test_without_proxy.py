#!/usr/bin/env python3
"""
Тест без прокси - используем urllib
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
    except urllib.error.HTTPError as e:
        print(f"❌ Legacy login ошибка: {e.code} - {e.reason}")
        print(f"Ответ: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    print("\n🔐 Тестируем новый API...")
    
    # Тест нового API
    req2 = urllib.request.Request(
        "http://localhost:8000/api/v1/auth/login",
        data=json_data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req2) as response:
            print(f"✅ Новый API login: {response.status}")
            data = response.read().decode('utf-8')
            print(f"Ответ: {data}")
    except urllib.error.HTTPError as e:
        print(f"❌ Новый API login ошибка: {e.code} - {e.reason}")
        print(f"Ответ: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == "__main__":
    test_login()

