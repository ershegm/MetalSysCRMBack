#!/usr/bin/env python3
import urllib.request
import json

# Тест обновления заказа
def test_update():
    print("Тестируем обновление заказа...")
    
    # Сначала получаем токен
    login_data = {"username": "admin", "password": "admin"}
    req = urllib.request.Request(
        "http://localhost:8000/api/auth/login",
        data=json.dumps(login_data).encode(),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = response.read().decode()
            result = json.loads(data)
            token = result.get('access_token')
            print(f"Токен получен: {token[:30]}...")
    except Exception as e:
        print(f"Ошибка входа: {e}")
        return
    
    # Тестируем обновление заказа
    update_data = {
        "status": "completed",
        "priority": "high"
    }
    
    update_req = urllib.request.Request(
        "http://localhost:8000/api/history/23",
        data=json.dumps(update_data).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(update_req) as response:
            print(f"Обновление: {response.status}")
            data = response.read().decode()
            result = json.loads(data)
            print(f"Ответ: {result}")
    except urllib.error.HTTPError as e:
        print(f"Ошибка обновления: {e.code}")
        error_data = e.read().decode()
        print(f"Детали: {error_data}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_update()
