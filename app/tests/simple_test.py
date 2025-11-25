#!/usr/bin/env python3
import urllib.request
import json

# Тест входа
login_data = {"username": "admin", "password": "admin"}
req = urllib.request.Request(
    "http://localhost:8000/api/auth/login",
    data=json.dumps(login_data).encode(),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req) as response:
        print(f"Вход: {response.status}")
        data = response.read().decode()
        result = json.loads(data)
        print(f"Ответ: {result}")
        
        if 'access_token' in result:
            token = result['access_token']
            print(f"Токен получен: {token[:30]}...")
            
            # Тест /api/auth/me
            me_req = urllib.request.Request(
                "http://localhost:8000/api/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            with urllib.request.urlopen(me_req) as me_response:
                print(f"/api/auth/me: {me_response.status}")
                me_data = me_response.read().decode()
                me_result = json.loads(me_data)
                print(f"Пользователь: {me_result}")
                
            # Тест /api/history
            hist_req = urllib.request.Request(
                "http://localhost:8000/api/history",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            with urllib.request.urlopen(hist_req) as hist_response:
                print(f"/api/history: {hist_response.status}")
                hist_data = hist_response.read().decode()
                hist_result = json.loads(hist_data)
                print(f"История: {len(hist_result)} заказов")
                
        else:
            print("Токен не получен")
            
except Exception as e:
    print(f"Ошибка: {e}")