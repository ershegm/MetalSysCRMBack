#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    # Отключаем прокси для локальных запросов
    session = requests.Session()
    session.proxies = {}
    
    print("🧪 Тестирование API...")
    
    # Тест 1: Корневой эндпоинт
    try:
        response = session.get(f"{base_url}/")
        print(f"✅ Корневой эндпоинт: {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.json()}")
    except Exception as e:
        print(f"❌ Корневой эндпоинт: {e}")
    
    # Тест 2: Health check
    try:
        response = session.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.json()}")
    except Exception as e:
        print(f"❌ Health check: {e}")
    
    # Тест 3: Legacy login
    try:
        login_data = {"username": "admin", "password": "admin"}
        response = session.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Legacy login: {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.json()}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Legacy login: {e}")
    
    # Тест 4: Новый API login
    try:
        login_data = {"username": "admin", "password": "admin"}
        response = session.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Новый API login: {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.json()}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Новый API login: {e}")
    
    # Тест 5: Legacy history
    try:
        response = session.get(f"{base_url}/api/history")
        print(f"✅ Legacy history: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Количество записей: {len(data) if isinstance(data, list) else 'N/A'}")
    except Exception as e:
        print(f"❌ Legacy history: {e}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_api()
