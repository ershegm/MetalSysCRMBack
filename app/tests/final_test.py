#!/usr/bin/env python3
import urllib.request
import json
import time

def test_all_functions():
    print("🚀 Тестируем все функции системы...")
    
    # Ждем запуска сервера
    print("⏳ Ждем запуска сервера...")
    time.sleep(2)
    
    # 1. Вход
    print("\n1. Тестируем вход...")
    try:
        login_data = {"username": "admin", "password": "admin"}
        req = urllib.request.Request(
            "http://localhost:8000/api/auth/login",
            data=json.dumps(login_data).encode(),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = response.read().decode()
                result = json.loads(data)
                token = result.get('access_token')
                print(f"✅ Вход успешен: {token[:30]}...")
            else:
                print(f"❌ Ошибка входа: {response.status}")
                return
    except Exception as e:
        print(f"❌ Ошибка входа: {e}")
        return
    
    # 2. Получение истории
    print("\n2. Тестируем получение истории...")
    try:
        req = urllib.request.Request(
            "http://localhost:8000/api/history",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = response.read().decode()
                result = json.loads(data)
                print(f"✅ История получена: {len(result)} заказов")
            else:
                print(f"❌ Ошибка истории: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка истории: {e}")
    
    # 3. Создание заказа
    print("\n3. Тестируем создание заказа...")
    try:
        proposal_data = {
            "productType": "Тестовое изделие",
            "material": "Сталь",
            "materialGrade": "Ст3",
            "dimensions": "100x50x10",
            "selectedOperations": "Резка, Сварка",
            "result": "Тестовый результат"
        }
        
        req = urllib.request.Request(
            "http://localhost:8000/api/history",
            data=json.dumps(proposal_data).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = response.read().decode()
                result = json.loads(data)
                print(f"✅ Заказ создан: ID {result.get('id', 'N/A')}")
            else:
                print(f"❌ Ошибка создания: {response.status}")
    except Exception as e:
        print(f"❌ Ошибка создания: {e}")
    
    # 4. Обновление заказа
    print("\n4. Тестируем обновление заказа...")
    try:
        update_data = {
            "status": "completed",
            "priority": "high"
        }
        
        req = urllib.request.Request(
            "http://localhost:8000/api/history/1",
            data=json.dumps(update_data).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            method="PUT"
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = response.read().decode()
                result = json.loads(data)
                print(f"✅ Заказ обновлен: {result.get('status', 'N/A')}")
            else:
                print(f"❌ Ошибка обновления: {response.status}")
                error_data = response.read().decode()
                print(f"   Детали: {error_data}")
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_all_functions()
