#!/usr/bin/env python3
"""
Полный тест API
"""
import urllib.request
import urllib.parse
import json

def test_api():
    print("🧪 Полное тестирование API...")
    
    # Тест 1: Корневой эндпоинт
    try:
        req = urllib.request.Request("http://localhost:8000/")
        with urllib.request.urlopen(req) as response:
            print(f"✅ Корневой эндпоинт: {response.status}")
            data = response.read().decode('utf-8')
            print(f"   Ответ: {data}")
    except Exception as e:
        print(f"❌ Корневой эндпоинт: {e}")
    
    # Тест 2: Health check
    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req) as response:
            print(f"✅ Health check: {response.status}")
            data = response.read().decode('utf-8')
            print(f"   Ответ: {data}")
    except Exception as e:
        print(f"❌ Health check: {e}")
    
    # Тест 3: Legacy login
    print("\n🔐 Тестируем вход в систему...")
    login_data = {"username": "admin", "password": "admin"}
    json_data = json.dumps(login_data).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/auth/login",
            data=json_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as response:
            print(f"✅ Legacy login: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"   Ответ: {result}")
            
            # Сохраняем токен для дальнейших тестов
            token = result.get('access_token')
            if token:
                print(f"   Токен получен: {token[:20]}...")
                
                # Тест 4: /api/auth/me с токеном
                try:
                    req_me = urllib.request.Request("http://localhost:8000/api/auth/me")
                    req_me.add_header("Authorization", f"Bearer {token}")
                    with urllib.request.urlopen(req_me) as response_me:
                        print(f"✅ /api/auth/me: {response_me.status}")
                        data_me = response_me.read().decode('utf-8')
                        print(f"   Ответ: {data_me}")
                except Exception as e:
                    print(f"❌ /api/auth/me: {e}")
            else:
                print("   ❌ Токен не получен")
                
    except Exception as e:
        print(f"❌ Legacy login: {e}")
    
    # Тест 5: Legacy history
    print("\n📋 Тестируем историю...")
    try:
        req = urllib.request.Request("http://localhost:8000/api/history")
        with urllib.request.urlopen(req) as response:
            print(f"✅ Legacy history: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"   Количество записей: {len(result) if isinstance(result, list) else 'N/A'}")
    except Exception as e:
        print(f"❌ Legacy history: {e}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_api()

