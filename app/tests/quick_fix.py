#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.core.database import db_manager

# Обновляем данные
with db_manager.get_connection() as conn:
    conn.execute("UPDATE proposals SET status = 'draft', priority = 'medium' WHERE status IS NULL OR status = '' OR priority IS NULL OR priority = ''")
    conn.execute("UPDATE proposals SET company = 'Тестовая компания' WHERE company IS NULL OR company = ''")
    conn.commit()
    print("Данные обновлены")
