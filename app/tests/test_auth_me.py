#!/usr/bin/env python3
"""
Тест /api/auth/me после исправления
"""
import urllib.request
import urllib.parse
import json

def test_auth_me():
    print("🔐 Тестируем /api/auth/me...")
    
    # 1. Сначала получаем токен
    print("\n1. Получаем токен...")
    login_data = {"username": "admin", "password": "admin"}
    json_data = json.dumps(login_data).encode('utf-8')
    
    login_req = urllib.request.Request(
        "http://localhost:8000/api/auth/login",
        data=json_data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(login_req) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                token = result.get('access_token')
                print(f"✅ Токен получен: {token[:30]}...")
            else:
                print(f"❌ Ошибка входа: {response.status}")
                return
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        return
    
    # 2. Тестируем /api/auth/me с токеном
    print("\n2. Тестируем /api/auth/me с токеном...")
    me_req = urllib.request.Request(
        "http://localhost:8000/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(me_req) as response:
            print(f"✅ /api/auth/me: {response.status}")
            data = response.read().decode('utf-8')
            result = json.loads(data)
            print(f"Ответ: {result}")
            
            if 'username' in result:
                print("🎉 /api/auth/me работает!")
                return True
            else:
                print("❌ Неожиданный ответ")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ /api/auth/me ошибка: {e.code} - {e.reason}")
        error_data = e.read().decode('utf-8')
        print(f"Ответ: {error_data}")
        return False
    except Exception as e:
        print(f"❌ Ошибка /api/auth/me: {e}")
        return False

if __name__ == "__main__":
    success = test_auth_me()
    if success:
        print("\n🎊 Проблема с /api/auth/me решена!")
    else:
        print("\n❌ Проблема с /api/auth/me все еще есть")
