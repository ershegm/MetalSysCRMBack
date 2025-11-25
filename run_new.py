#!/usr/bin/env python3
"""
Скрипт для запуска новой архитектуры
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        import uvicorn
        from app.main import app
        
        print("🚀 Запуск Proflans Metal Host API v2.0")
        print("📁 Новая Enterprise архитектура")
        print("🔗 API документация: http://localhost:8000/docs")
        print("❤️  Health check: http://localhost:8000/health")
        print("-" * 50)
        
        print("📦 Импорт uvicorn успешен")
        print("📦 Импорт app успешен")
        print("🚀 Запускаем сервер...")
        
        uvicorn.run(
            app,  # Используем объект приложения напрямую
            host="0.0.0.0",
            port=8000,
            reload=False,  # Отключаем reload для стабильности
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()

