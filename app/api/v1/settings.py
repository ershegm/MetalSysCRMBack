"""
API роуты для настроек сайдбара
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from ...core.database import DatabaseManager
from ...core.security import get_current_user

router = APIRouter()

# Создаем экземпляр DatabaseManager
db_manager = DatabaseManager()


class SidebarSettingsUpdate(BaseModel):
    """Модель для обновления настроек сайдбара"""
    hidden_categories: List[str] = []
    collapsed_categories: List[str] = []
    hidden_items: List[str] = []


class SidebarSettingsResponse(BaseModel):
    """Модель ответа с настройками сайдбара"""
    hidden_categories: List[str]
    collapsed_categories: List[str]
    hidden_items: List[str]


def init_sidebar_settings_table():
    """Инициализация таблицы настроек сайдбара"""
    with db_manager.get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sidebar_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hidden_categories TEXT DEFAULT '[]',
                collapsed_categories TEXT DEFAULT '[]',
                hidden_items TEXT DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем запись по умолчанию, если её нет
        cursor = conn.execute('SELECT * FROM sidebar_settings WHERE id = 1')
        if not cursor.fetchone():
            conn.execute('''
                INSERT INTO sidebar_settings (id, hidden_categories, collapsed_categories, hidden_items)
                VALUES (1, '[]', '[]', '[]')
            ''')
        
        conn.commit()


@router.get("/sidebar", response_model=SidebarSettingsResponse)
async def get_sidebar_settings(
    current_user: dict = Depends(get_current_user)
):
    """Получение настроек сайдбара (глобальные настройки)"""
    init_sidebar_settings_table()
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute('SELECT * FROM sidebar_settings WHERE id = 1')
        row = cursor.fetchone()
        
        if not row:
            # Если записи нет, создаем её
            conn.execute('''
                INSERT INTO sidebar_settings (id, hidden_categories, collapsed_categories, hidden_items)
                VALUES (1, '[]', '[]', '[]')
            ''')
            conn.commit()
            return SidebarSettingsResponse(
                hidden_categories=[],
                collapsed_categories=[],
                hidden_items=[]
            )
        
        import json
        return SidebarSettingsResponse(
            hidden_categories=json.loads(row[1] or '[]'),
            collapsed_categories=json.loads(row[2] or '[]'),
            hidden_items=json.loads(row[3] or '[]')
        )


@router.put("/sidebar", response_model=SidebarSettingsResponse)
async def update_sidebar_settings(
    settings: SidebarSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновление настроек сайдбара (глобальные настройки)"""
    init_sidebar_settings_table()
    
    import json
    with db_manager.get_connection() as conn:
        # Проверяем, существует ли запись
        cursor = conn.execute('SELECT * FROM sidebar_settings WHERE id = 1')
        row = cursor.fetchone()
        
        if not row:
            # Создаем запись, если её нет
            conn.execute('''
                INSERT INTO sidebar_settings (id, hidden_categories, collapsed_categories, hidden_items)
                VALUES (1, ?, ?, ?)
            ''', (
                json.dumps(settings.hidden_categories),
                json.dumps(settings.collapsed_categories),
                json.dumps(settings.hidden_items)
            ))
        else:
            # Обновляем существующую запись
            conn.execute('''
                UPDATE sidebar_settings
                SET hidden_categories = ?,
                    collapsed_categories = ?,
                    hidden_items = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (
                json.dumps(settings.hidden_categories),
                json.dumps(settings.collapsed_categories),
                json.dumps(settings.hidden_items)
            ))
        
        conn.commit()
        
        return SidebarSettingsResponse(
            hidden_categories=settings.hidden_categories,
            collapsed_categories=settings.collapsed_categories,
            hidden_items=settings.hidden_items
        )

