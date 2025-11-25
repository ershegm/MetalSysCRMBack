"""
Хелперы для работы с JSON файлами и SQLite
"""
import json
import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import sqlite3


def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Читает JSON файл и возвращает список словарей
    
    Args:
        file_path: Путь к JSON файлу
        
    Returns:
        Список словарей из JSON файла (пустой список если файл не существует или ошибка)
    """
    try:
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Ошибка чтения JSON файла {file_path}: {e}")
        return []


def write_json_file(file_path: str, data: List[Dict[str, Any]]) -> bool:
    """
    Атомарно записывает данные в JSON файл (через временный файл)
    
    Args:
        file_path: Путь к JSON файлу
        data: Список словарей для записи
        
    Returns:
        True если запись успешна, False иначе
    """
    try:
        # Создаём директорию если её нет
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        # Записываем во временный файл
        temp_file = None
        try:
            # Создаём временный файл в той же директории
            temp_dir = os.path.dirname(file_path) or '.'
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=temp_dir, delete=False, suffix='.json.tmp') as f:
                temp_file = f.name
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Атомарно заменяем оригинальный файл
            if os.path.exists(file_path):
                shutil.move(temp_file, file_path)
            else:
                shutil.move(temp_file, file_path)
            
            return True
        except Exception as e:
            # Удаляем временный файл при ошибке
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise e
    except (IOError, OSError, json.JSONEncodeError) as e:
        print(f"Ошибка записи JSON файла {file_path}: {e}")
        return False


@contextmanager
def get_sqlite_connection(db_path: str):
    """
    Контекстный менеджер для работы с SQLite
    
    Args:
        db_path: Путь к файлу базы данных SQLite
        
    Yields:
        sqlite3.Connection: Соединение с базой данных
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def next_id(items: List[Dict[str, Any]], id_key: str = 'id') -> int:
    """
    Генерирует следующий ID для списка словарей
    
    Args:
        items: Список словарей
        id_key: Ключ для ID (по умолчанию 'id')
        
    Returns:
        Следующий ID (максимальный + 1, или 1 если список пустой)
    """
    if not items:
        return 1
    max_id = max((item.get(id_key, 0) for item in items), default=0)
    return max_id + 1


def generate_external_id(prefix: str, id: int) -> str:
    """
    Генерирует external_id для сущности
    
    Args:
        prefix: Префикс (например, 'customer', 'contact', 'deal')
        id: ID сущности
        
    Returns:
        external_id в формате "{prefix}_{id}"
    """
    return f"{prefix}_{id}"




