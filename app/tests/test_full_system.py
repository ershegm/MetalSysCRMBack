#!/usr/bin/env python3
"""
Тест полной функциональности системы
"""
import urllib.request
import urllib.parse
import json

def test_full_system():
    print("🚀 Тестируем полную функциональность системы...")
    
    # 1. Вход в систему
    print("\n1. Тестируем вход в систему...")
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
                print(f"✅ Вход успешен, токен: {token[:30]}...")
            else:
                print(f"❌ Ошибка входа: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        return False
    
    # 2. Проверяем информацию о пользователе
    print("\n2. Проверяем /api/auth/me...")
    me_req = urllib.request.Request(
        "http://localhost:8000/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(me_req) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                print(f"✅ Информация о пользователе: {result['username']}")
            else:
                print(f"❌ Ошибка /api/auth/me: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Ошибка /api/auth/me: {e}")
        return False
    
    # 3. Получаем историю заказов
    print("\n3. Получаем историю заказов...")
    history_req = urllib.request.Request(
        "http://localhost:8000/api/history",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(history_req) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                print(f"✅ История заказов получена: {len(result)} заказов")
                if result:
                    print(f"   Первый заказ: {result[0].get('productType', 'N/A')}")
            else:
                print(f"❌ Ошибка /api/history: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Ошибка /api/history: {e}")
        return False
    
    # 4. Тестируем создание заказа
    print("\n4. Тестируем создание заказа...")
    proposal_data = {
        "user_id": 1,
        "productType": "Тестовое изделие",
        "material": "Сталь",
        "materialGrade": "Ст3",
        "dimensions": "100x50x10",
        "selectedOperations": "Резка, Сварка",
        "result": "Тестовый результат",
        "status": "pending",
        "priority": "medium"
    }
    
    create_req = urllib.request.Request(
        "http://localhost:8000/api/history",
        data=json.dumps(proposal_data).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(create_req) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                result = json.loads(data)
                print(f"✅ Заказ создан: ID {result.get('id', 'N/A')}")
            else:
                print(f"❌ Ошибка создания заказа: {response.status}")
                error_data = response.read().decode('utf-8')
                print(f"   Ответ: {error_data}")
                return False
    except Exception as e:
        print(f"❌ Ошибка создания заказа: {e}")
        return False
    
    print("\n🎉 Все тесты прошли успешно!")
    return True

if __name__ == "__main__":
    success = test_full_system()
    if success:
        print("\n🎊 Система полностью работает!")
    else:
        print("\n❌ Есть проблемы в системе")
