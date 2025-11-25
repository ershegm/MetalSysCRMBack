"""
Сервис для работы с воронками продаж (funnels)
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.database import db_manager
from ..utils.constants import SYSTEM_STAGES, DEFAULT_FUNNEL_NAME, DEFAULT_FUNNEL_DESCRIPTION
from ..utils.enums import StageSemanticId


class FunnelService:
    """Сервис для работы с воронками через SQLite"""
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Получает список всех воронок"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM funnels ORDER BY is_default DESC, created_at DESC')
            funnels = []
            for row in cursor.fetchall():
                funnel = dict(row)
                # Получаем стадии для каждой воронки
                stages_cursor = conn.execute(
                    'SELECT * FROM deal_stages WHERE funnel_id = ? ORDER BY order_index ASC',
                    (funnel['id'],)
                )
                stages = [dict(row) for row in stages_cursor.fetchall()]
                funnel['stages'] = stages
                funnels.append(funnel)
            return funnels
    
    def get_by_id(self, funnel_id: int) -> Optional[Dict[str, Any]]:
        """Получает воронку по ID со стадиями и метриками"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM funnels WHERE id = ?', (funnel_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            funnel = dict(row)
            
            # Получаем стадии
            stages_cursor = conn.execute(
                'SELECT * FROM deal_stages WHERE funnel_id = ? ORDER BY order_index ASC',
                (funnel_id,)
            )
            stages = []
            for stage_row in stages_cursor.fetchall():
                stage = dict(stage_row)
                
                # Получаем метрики для стадии
                metrics_cursor = conn.execute(
                    'SELECT * FROM stage_metrics WHERE stage_id = ?',
                    (stage['id'],)
                )
                metrics_row = metrics_cursor.fetchone()
                if metrics_row:
                    stage['metrics'] = dict(metrics_row)
                
                stages.append(stage)
            
            funnel['stages'] = stages
            return funnel
    
    def get_default(self) -> Optional[Dict[str, Any]]:
        """Получает воронку по умолчанию"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM funnels WHERE is_default = TRUE LIMIT 1')
            row = cursor.fetchone()
            if row:
                return self.get_by_id(row['id'])
            
            # Если нет воронки по умолчанию, возвращаем первую
            cursor = conn.execute('SELECT * FROM funnels ORDER BY created_at ASC LIMIT 1')
            row = cursor.fetchone()
            if row:
                return self.get_by_id(row['id'])
            
            return None
    
    def create(self, funnel_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Создаёт новую воронку
        
        Args:
            funnel_data: Данные воронки
            user_id: ID пользователя, создающего воронку
            
        Returns:
            Созданная воронка
        """
        with db_manager.get_connection() as conn:
            name = funnel_data.get('name', '')
            description = funnel_data.get('description')
            is_default = funnel_data.get('is_default', False)
            
            # Если устанавливаем как default, снимаем флаг с других
            if is_default:
                conn.execute('UPDATE funnels SET is_default = FALSE')
            
            cursor = conn.execute('''
                INSERT INTO funnels (name, description, is_default, created_by_id, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, is_default, user_id, True))
            
            funnel_id = cursor.lastrowid
            
            # Если это первая воронка или is_default, создаём системные стадии
            if is_default or not self.get_all():
                self._create_system_stages(conn, funnel_id)
            
            conn.commit()
            return self.get_by_id(funnel_id)
    
    def update(self, funnel_id: int, funnel_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновляет воронку"""
        with db_manager.get_connection() as conn:
            # Проверяем существование воронки
            cursor = conn.execute('SELECT * FROM funnels WHERE id = ?', (funnel_id,))
            if not cursor.fetchone():
                return None
            
            updates = []
            values = []
            
            if 'name' in funnel_data:
                updates.append('name = ?')
                values.append(funnel_data['name'])
            
            if 'description' in funnel_data:
                updates.append('description = ?')
                values.append(funnel_data['description'])
            
            if 'is_default' in funnel_data:
                is_default = funnel_data['is_default']
                # Если устанавливаем как default, снимаем флаг с других
                if is_default:
                    conn.execute('UPDATE funnels SET is_default = FALSE WHERE id != ?', (funnel_id,))
                updates.append('is_default = ?')
                values.append(is_default)
            
            if 'is_active' in funnel_data:
                updates.append('is_active = ?')
                values.append(funnel_data['is_active'])
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                values.append(funnel_id)
                sql = f"UPDATE funnels SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, values)
                conn.commit()
            
            return self.get_by_id(funnel_id)
    
    def delete(self, funnel_id: int) -> bool:
        """Удаляет воронку (нельзя удалить default)"""
        with db_manager.get_connection() as conn:
            # Проверяем что воронка не является default
            cursor = conn.execute('SELECT is_default FROM funnels WHERE id = ?', (funnel_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            if row['is_default']:
                raise ValueError('Нельзя удалить воронку по умолчанию')
            
            # Удаляем воронку (стадии удалятся каскадно)
            cursor = conn.execute('DELETE FROM funnels WHERE id = ?', (funnel_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_stage(self, funnel_id: int, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Добавляет стадию к воронке"""
        with db_manager.get_connection() as conn:
            # Получаем максимальный order_index
            cursor = conn.execute(
                'SELECT MAX(order_index) as max_order FROM deal_stages WHERE funnel_id = ?',
                (funnel_id,)
            )
            row = cursor.fetchone()
            max_order = (row['max_order'] or -1) + 1
            
            cursor = conn.execute('''
                INSERT INTO deal_stages (
                    funnel_id, stage_id, name, label, description,
                    color_text, color_bg, color_border, order_index,
                    is_system, stage_semantic_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                funnel_id,
                stage_data.get('stage_id'),
                stage_data.get('name'),
                stage_data.get('label'),
                stage_data.get('description'),
                stage_data.get('color_text'),
                stage_data.get('color_bg'),
                stage_data.get('color_border'),
                stage_data.get('order_index', max_order),
                stage_data.get('is_system', False),
                stage_data.get('stage_semantic_id', 'P'),
            ))
            
            stage_id = cursor.lastrowid
            
            # Создаём метрики для стадии
            conn.execute('''
                INSERT INTO stage_metrics (stage_id)
                VALUES (?)
            ''', (stage_id,))
            
            conn.commit()
            
            # Возвращаем созданную стадию
            cursor = conn.execute('SELECT * FROM deal_stages WHERE id = ?', (stage_id,))
            return dict(cursor.fetchone())
    
    def update_stage(self, funnel_id: int, stage_id: int, stage_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновляет стадию"""
        with db_manager.get_connection() as conn:
            # Проверяем что стадия принадлежит воронке
            cursor = conn.execute(
                'SELECT * FROM deal_stages WHERE id = ? AND funnel_id = ?',
                (stage_id, funnel_id)
            )
            if not cursor.fetchone():
                return None
            
            updates = []
            values = []
            
            for field in ['name', 'label', 'description', 'color_text', 'color_bg', 'color_border', 'order_index', 'stage_semantic_id']:
                if field in stage_data:
                    updates.append(f'{field} = ?')
                    values.append(stage_data[field])
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                values.extend([stage_id, funnel_id])
                sql = f"UPDATE deal_stages SET {', '.join(updates)} WHERE id = ? AND funnel_id = ?"
                conn.execute(sql, values)
                conn.commit()
            
            cursor = conn.execute('SELECT * FROM deal_stages WHERE id = ?', (stage_id,))
            return dict(cursor.fetchone())
    
    def delete_stage(self, funnel_id: int, stage_id: int) -> bool:
        """
        Удаляет стадию (перемещает все сделки в первую стадию воронки)
        
        Args:
            funnel_id: ID воронки
            stage_id: ID стадии для удаления
            
        Returns:
            True если успешно удалено
        """
        with db_manager.get_connection() as conn:
            # Получаем первую стадию воронки
            cursor = conn.execute(
                'SELECT id FROM deal_stages WHERE funnel_id = ? ORDER BY order_index ASC LIMIT 1',
                (funnel_id,)
            )
            first_stage_row = cursor.fetchone()
            if not first_stage_row:
                return False
            
            first_stage_id = first_stage_row['id']
            
            # Перемещаем все сделки в первую стадию
            conn.execute('''
                UPDATE deals SET stage_id = ?, moved_at = CURRENT_TIMESTAMP
                WHERE funnel_id = ? AND stage_id = ?
            ''', (first_stage_id, funnel_id, stage_id))
            
            # Удаляем метрики стадии
            conn.execute('DELETE FROM stage_metrics WHERE stage_id = ?', (stage_id,))
            
            # Удаляем стадию
            cursor = conn.execute(
                'DELETE FROM deal_stages WHERE id = ? AND funnel_id = ?',
                (stage_id, funnel_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def reorder_stages(self, funnel_id: int, stage_ids: List[int]) -> bool:
        """
        Изменяет порядок стадий в воронке
        
        Args:
            funnel_id: ID воронки
            stage_ids: Список ID стадий в новом порядке
            
        Returns:
            True если успешно обновлено
        """
        with db_manager.get_connection() as conn:
            # Сначала устанавливаем все order_index в отрицательные значения, чтобы избежать конфликтов UNIQUE
            for stage_id in stage_ids:
                conn.execute('''
                    UPDATE deal_stages SET order_index = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND funnel_id = ?
                ''', (-stage_id - 10000, stage_id, funnel_id))
            
            # Теперь устанавливаем правильные значения order_index
            for order_index, stage_id in enumerate(stage_ids):
                conn.execute('''
                    UPDATE deal_stages SET order_index = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND funnel_id = ?
                ''', (order_index, stage_id, funnel_id))
            
            conn.commit()
            return True
    
    def set_default(self, funnel_id: int) -> Optional[Dict[str, Any]]:
        """Устанавливает воронку как стандартную"""
        with db_manager.get_connection() as conn:
            # Снимаем флаг default со всех воронок
            conn.execute('UPDATE funnels SET is_default = FALSE')
            
            # Устанавливаем флаг default для указанной воронки
            conn.execute('UPDATE funnels SET is_default = TRUE, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (funnel_id,))
            conn.commit()
            
            return self.get_by_id(funnel_id)
    
    def _create_system_stages(self, conn, funnel_id: int) -> None:
        """Создаёт системные стадии для воронки"""
        for stage_key, stage_config in SYSTEM_STAGES.items():
            # Проверяем что стадия ещё не существует
            cursor = conn.execute(
                'SELECT id FROM deal_stages WHERE funnel_id = ? AND stage_id = ?',
                (funnel_id, stage_config['stage_id'])
            )
            if cursor.fetchone():
                continue
            
            cursor = conn.execute('''
                INSERT INTO deal_stages (
                    funnel_id, stage_id, name, label, description,
                    color_text, color_bg, color_border, order_index,
                    is_system, stage_semantic_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                funnel_id,
                stage_config['stage_id'],
                stage_config['name'],
                stage_config.get('label'),
                stage_config.get('description'),
                stage_config['color_text'],
                stage_config['color_bg'],
                stage_config['color_border'],
                stage_config['order_index'],
                stage_config['is_system'],
                stage_config['stage_semantic_id'],
            ))
            
            stage_id = cursor.lastrowid
            
            # Создаём метрики для стадии
            conn.execute('''
                INSERT INTO stage_metrics (stage_id)
                VALUES (?)
            ''', (stage_id,))
        
        conn.commit()




