"""
Сервис для работы со сделками (deals)
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from ..core.database import db_manager
from ..utils.enums import ChangeType, FileType
from ..utils.constants import DEFAULT_CURRENCY


class DealService:
    """Сервис для работы со сделками через SQLite"""
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        funnel_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        company_id: Optional[int] = None,
        responsible_user_id: Optional[int] = None,
        primary_contact_id: Optional[int] = None,
        is_closed: Optional[bool] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Получает список всех сделок с фильтрацией
        
        Args:
            skip: Пропустить записей
            limit: Лимит записей
            funnel_id: Фильтр по воронке
            stage_id: Фильтр по стадии
            company_id: Фильтр по компании
            responsible_user_id: Фильтр по ответственному менеджеру
            primary_contact_id: Фильтр по основному контакту
            is_closed: Фильтр по статусу закрытия
            date_from: Фильтр по дате начала (от)
            date_to: Фильтр по дате начала (до)
            
        Returns:
            Кортеж (список сделок, общее количество)
        """
        with db_manager.get_connection() as conn:
            # Строим запрос с фильтрами
            query = 'SELECT * FROM deals WHERE 1=1'
            params = []
            
            if funnel_id is not None:
                query += ' AND funnel_id = ?'
                params.append(funnel_id)
            
            if stage_id is not None:
                query += ' AND stage_id = ?'
                params.append(stage_id)
            
            if company_id is not None:
                query += ' AND company_id = ?'
                params.append(company_id)
            
            if responsible_user_id is not None:
                query += ' AND responsible_user_id = ?'
                params.append(responsible_user_id)
            
            if primary_contact_id is not None:
                query += ' AND primary_contact_id = ?'
                params.append(primary_contact_id)
            
            if is_closed is not None:
                query += ' AND is_closed = ?'
                params.append(is_closed)
            
            if date_from is not None:
                query += ' AND start_date >= ?'
                params.append(date_from.isoformat())
            
            if date_to is not None:
                query += ' AND start_date <= ?'
                params.append(date_to.isoformat())
            
            # Подсчёт общего количества
            count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Получаем данные с пагинацией
            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, skip])
            
            cursor = conn.execute(query, params)
            deals = [dict(row) for row in cursor.fetchall()]
            
            # Обогащаем данными
            enriched = [self._enrich_deal(conn, deal) for deal in deals]
            
            return enriched, total
    
    def get_by_id(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """Получает сделку по ID со всеми связанными данными"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            deal = dict(row)
            return self._enrich_deal(conn, deal)
    
    def create(self, deal_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Создаёт новую сделку
        
        Args:
            deal_data: Данные сделки
            user_id: ID пользователя, создающего сделку
            
        Returns:
            Созданная сделка
        """
        with db_manager.get_connection() as conn:
            # Генерируем номер сделки
            cursor = conn.execute('SELECT MAX(id) as max_id FROM deals')
            row = cursor.fetchone()
            max_id = row['max_id'] or 0
            deal_number = f"Сделка #{max_id + 1}"
            
            # Генерируем external_id
            external_id = f"deal_{max_id + 1}"
            
            # Извлекаем даты
            start_date = deal_data.get('start_date')
            if start_date and isinstance(start_date, str):
                start_date = start_date
            elif start_date and isinstance(start_date, date):
                start_date = start_date.isoformat()
            
            close_date = deal_data.get('close_date')
            if close_date and isinstance(close_date, str):
                close_date = close_date
            elif close_date and isinstance(close_date, date):
                close_date = close_date.isoformat()
            
            cursor = conn.execute('''
                INSERT INTO deals (
                    external_id, deal_number, title, description, deal_type,
                    funnel_id, stage_id, amount, currency_id, probability_percent,
                    is_manual_amount, tax_value, start_date, close_date,
                    company_id, primary_contact_id, responsible_user_id,
                    is_closed, is_public, is_new, is_recurring, recurrence_pattern,
                    source_id, source_description, utm_source, utm_medium,
                    utm_campaign, utm_content, utm_term, created_by_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                external_id,
                deal_number,
                deal_data.get('title', ''),
                deal_data.get('description'),
                deal_data.get('deal_type', 'SALE'),
                deal_data.get('funnel_id'),
                deal_data.get('stage_id'),
                deal_data.get('amount', 0),
                deal_data.get('currency_id', DEFAULT_CURRENCY),
                deal_data.get('probability_percent', 50),
                deal_data.get('is_manual_amount', False),
                deal_data.get('tax_value', 0),
                start_date,
                close_date,
                deal_data.get('company_id'),
                deal_data.get('primary_contact_id'),
                deal_data.get('responsible_user_id', user_id),
                deal_data.get('is_closed', False),
                deal_data.get('is_public', True),
                deal_data.get('is_new', True),
                deal_data.get('is_recurring', False),
                deal_data.get('recurrence_pattern'),
                deal_data.get('source_id'),
                deal_data.get('source_description'),
                deal_data.get('utm_source'),
                deal_data.get('utm_medium'),
                deal_data.get('utm_campaign'),
                deal_data.get('utm_content'),
                deal_data.get('utm_term'),
                user_id,
            ))
            
            deal_id = cursor.lastrowid
            
            # Логируем создание в историю
            self._log_history(conn, deal_id, 'deal_created', None, deal_data.get('title', ''), ChangeType.CREATE, user_id)
            
            conn.commit()
            return self.get_by_id(deal_id)
    
    def update(self, deal_id: int, deal_data: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
        """
        Обновляет сделку с логированием изменений
        
        Args:
            deal_id: ID сделки
            deal_data: Данные для обновления
            user_id: ID пользователя, обновляющего сделку
            
        Returns:
            Обновлённая сделка
        """
        with db_manager.get_connection() as conn:
            # Получаем текущую сделку
            cursor = conn.execute('SELECT * FROM deals WHERE id = ?', (deal_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            old_deal = dict(row)
            
            # Подготавливаем изменения
            updates = []
            values = []
            changes = {}
            
            update_fields = {
                'title', 'description', 'deal_type', 'funnel_id', 'stage_id',
                'amount', 'currency_id', 'probability_percent', 'is_manual_amount',
                'tax_value', 'start_date', 'close_date', 'company_id',
                'primary_contact_id', 'responsible_user_id', 'is_closed',
                'is_public', 'is_new', 'is_recurring', 'recurrence_pattern',
                'source_id', 'source_description', 'utm_source', 'utm_medium',
                'utm_campaign', 'utm_content', 'utm_term'
            }
            
            for field in update_fields:
                if field in deal_data:
                    value = deal_data[field]
                    
                    # Обработка дат
                    if field in ('start_date', 'close_date') and value:
                        if isinstance(value, date):
                            value = value.isoformat()
                    
                    old_value = old_deal.get(field)
                    if old_value != value:
                        changes[field] = (old_value, value)
                        updates.append(f'{field} = ?')
                        values.append(value)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                updates.append('modified_by_id = ?')
                values.extend([user_id, deal_id])
                
                sql = f"UPDATE deals SET {', '.join(updates)} WHERE id = ?"
                conn.execute(sql, values)
                
                # Логируем изменения в историю
                for field, (old_val, new_val) in changes.items():
                    self._log_history(conn, deal_id, field, str(old_val) if old_val is not None else None, str(new_val) if new_val is not None else None, ChangeType.UPDATE, user_id)
                
                conn.commit()
            
            return self.get_by_id(deal_id)
    
    def delete(self, deal_id: int, user_id: int) -> bool:
        """
        Удаляет сделку с логированием
        
        Args:
            deal_id: ID сделки
            user_id: ID пользователя, удаляющего сделку
            
        Returns:
            True если успешно удалено
        """
        with db_manager.get_connection() as conn:
            # Логируем удаление
            deal = self.get_by_id(deal_id)
            if deal:
                self._log_history(conn, deal_id, 'deal_deleted', deal.get('title'), None, ChangeType.DELETE, user_id)
            
            # Удаляем сделку (связанные данные удалятся каскадно)
            cursor = conn.execute('DELETE FROM deals WHERE id = ?', (deal_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def move_to_stage(self, deal_id: int, stage_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Перемещает сделку на другую стадию
        
        Args:
            deal_id: ID сделки
            stage_id: ID новой стадии
            user_id: ID пользователя, перемещающего сделку
            
        Returns:
            Обновлённая сделка
        """
        with db_manager.get_connection() as conn:
            # Получаем текущую стадию
            cursor = conn.execute('SELECT stage_id FROM deals WHERE id = ?', (deal_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            old_stage_id = row['stage_id']
            
            if old_stage_id == stage_id:
                return self.get_by_id(deal_id)
            
            # Обновляем стадию
            conn.execute('''
                UPDATE deals
                SET stage_id = ?, moved_at = CURRENT_TIMESTAMP, moved_by_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (stage_id, user_id, deal_id))
            
            # Логируем изменение стадии
            self._log_history(conn, deal_id, 'stage', str(old_stage_id), str(stage_id), ChangeType.STAGE_CHANGE, user_id)
            
            conn.commit()
            return self.get_by_id(deal_id)
    
    def add_product(self, deal_id: int, product_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Добавляет товар к сделке
        
        Args:
            deal_id: ID сделки
            product_data: Данные товара
            user_id: ID пользователя, добавляющего товар
            
        Returns:
            Добавленный товар
        """
        with db_manager.get_connection() as conn:
            price = float(product_data.get('price', 0))
            quantity = float(product_data.get('quantity', 1))
            discount_percent = float(product_data.get('discount_percent', 0))
            tax_percent = float(product_data.get('tax_percent', 0))
            
            # Рассчитываем line_total
            line_total = price * quantity * (1 - discount_percent / 100) * (1 + tax_percent / 100)
            
            cursor = conn.execute('''
                INSERT INTO deal_products (
                    deal_id, product_id, name, description, price, quantity, unit,
                    discount_percent, tax_percent, line_total, added_by_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deal_id,
                product_data.get('product_id'),
                product_data.get('name', ''),
                product_data.get('description'),
                price,
                quantity,
                product_data.get('unit', 'шт'),
                discount_percent,
                tax_percent,
                line_total,
                user_id,
            ))
            
            product_id = cursor.lastrowid
            
            # Пересчитываем сумму сделки если не manual
            self._recalculate_deal_amount(conn, deal_id)
            
            conn.commit()
            
            # Возвращаем созданный товар
            cursor = conn.execute('SELECT * FROM deal_products WHERE id = ?', (product_id,))
            return dict(cursor.fetchone())
    
    def remove_product(self, deal_id: int, product_id: int) -> bool:
        """Удаляет товар из сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                'DELETE FROM deal_products WHERE id = ? AND deal_id = ?',
                (product_id, deal_id)
            )
            
            # Пересчитываем сумму сделки если не manual
            self._recalculate_deal_amount(conn, deal_id)
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_products(self, deal_id: int) -> List[Dict[str, Any]]:
        """Получает список товаров сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM deal_products WHERE deal_id = ? ORDER BY added_at ASC',
                (deal_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def upload_file(
        self,
        deal_id: int,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
        mime_type: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Загружает файл к сделке с версионированием
        
        Args:
            deal_id: ID сделки
            file_name: Имя файла
            file_path: Относительный путь/URL к файлу
            file_type: Тип файла (QUOTE, INVOICE, CONTRACT, etc.)
            file_size: Размер файла в байтах
            mime_type: MIME тип
            user_id: ID пользователя, загружающего файл
            
        Returns:
            Информация о загруженном файле
        """
        with db_manager.get_connection() as conn:
            parent_version_id = None
            version_number = 1
            
            if file_type == FileType.QUOTE:
                cursor = conn.execute('''
                    SELECT id, version_number
                    FROM deal_files
                    WHERE deal_id = ? AND file_type = ? AND is_current = TRUE
                    ORDER BY version_number DESC
                    LIMIT 1
                ''', (deal_id, file_type))
                current_file = cursor.fetchone()
                if current_file:
                    parent_version_id = current_file['id']
                    version_number = (current_file['version_number'] or 0) + 1
                    conn.execute('UPDATE deal_files SET is_current = FALSE WHERE id = ?', (parent_version_id,))
                else:
                    version_number = 1
            
            cursor = conn.execute('''
                INSERT INTO deal_files (
                    deal_id, file_name, file_path, file_type, file_size,
                    mime_type, version_number, is_current, parent_version_id,
                    uploaded_by_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                deal_id,
                file_name,
                file_path,
                file_type,
                file_size,
                mime_type,
                version_number,
                True,
                parent_version_id,
                user_id,
            ))
            
            file_id = cursor.lastrowid
            
            self._log_history(
                conn,
                deal_id,
                'file_uploaded',
                None,
                f"{file_type}: {file_name}",
                ChangeType.FILE_ADDED,
                user_id
            )
            
            conn.commit()
            cursor = conn.execute('SELECT * FROM deal_files WHERE id = ?', (file_id,))
            return dict(cursor.fetchone())
    
    def get_files(self, deal_id: int) -> List[Dict[str, Any]]:
        """Получает список файлов сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM deal_files
                WHERE deal_id = ? AND is_deleted = FALSE
                ORDER BY uploaded_at DESC
            ''', (deal_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_file(self, deal_id: int, file_id: int) -> bool:
        """Удаляет файл (soft delete)"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE deal_files
                SET is_deleted = TRUE
                WHERE id = ? AND deal_id = ?
            ''', (file_id, deal_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def add_comment(self, deal_id: int, text: str, user_id: int, parent_comment_id: Optional[int] = None) -> Dict[str, Any]:
        """Добавляет комментарий к сделке"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO deal_comments (deal_id, author_id, text, parent_comment_id)
                VALUES (?, ?, ?, ?)
            ''', (deal_id, user_id, text, parent_comment_id))
            
            comment_id = cursor.lastrowid
            conn.commit()
            
            # Возвращаем созданный комментарий
            cursor = conn.execute('SELECT * FROM deal_comments WHERE id = ?', (comment_id,))
            return dict(cursor.fetchone())
    
    def get_comments(self, deal_id: int) -> List[Dict[str, Any]]:
        """Получает список комментариев сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM deal_comments
                WHERE deal_id = ? AND is_deleted = FALSE
                ORDER BY created_at ASC
            ''', (deal_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_comment(self, deal_id: int, comment_id: int) -> bool:
        """Удаляет комментарий (soft delete)"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE deal_comments
                SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deal_id = ?
            ''', (comment_id, deal_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_history(self, deal_id: int) -> List[Dict[str, Any]]:
        """Получает историю изменений сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM deal_history
                WHERE deal_id = ?
                ORDER BY changed_at DESC
            ''', (deal_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_participant(self, deal_id: int, contact_id: Optional[int], user_id: Optional[int], participant_type: str) -> Dict[str, Any]:
        """Добавляет участника к сделке (с проверкой уникальности на уровне приложения)"""
        with db_manager.get_connection() as conn:
            # Проверяем, не существует ли уже такой участник
            if contact_id is not None:
                cursor = conn.execute('''
                    SELECT id FROM deal_participants
                    WHERE deal_id = ? AND contact_id = ?
                ''', (deal_id, contact_id))
                if cursor.fetchone():
                    raise ValueError(f'Контакт {contact_id} уже является участником сделки {deal_id}')
            
            if user_id is not None:
                cursor = conn.execute('''
                    SELECT id FROM deal_participants
                    WHERE deal_id = ? AND user_id = ?
                ''', (deal_id, user_id))
                if cursor.fetchone():
                    raise ValueError(f'Пользователь {user_id} уже является участником сделки {deal_id}')
            
            # Если оба None, это ошибка
            if contact_id is None and user_id is None:
                raise ValueError('Необходимо указать либо contact_id, либо user_id')
            
            cursor = conn.execute('''
                INSERT INTO deal_participants (deal_id, contact_id, user_id, participant_type)
                VALUES (?, ?, ?, ?)
            ''', (deal_id, contact_id, user_id, participant_type))
            
            participant_id = cursor.lastrowid
            conn.commit()
            
            # Возвращаем созданного участника
            cursor = conn.execute('SELECT * FROM deal_participants WHERE id = ?', (participant_id,))
            return dict(cursor.fetchone())
    
    def remove_participant(self, deal_id: int, participant_id: int) -> bool:
        """Удаляет участника из сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM deal_participants
                WHERE id = ? AND deal_id = ?
            ''', (participant_id, deal_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_participants(self, deal_id: int) -> List[Dict[str, Any]]:
        """Получает список участников сделки"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM deal_participants
                WHERE deal_id = ?
                ORDER BY joined_at ASC
            ''', (deal_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def _recalculate_deal_amount(self, conn, deal_id: int) -> None:
        """Пересчитывает сумму сделки из товаров (если не is_manual_amount)"""
        cursor = conn.execute('SELECT is_manual_amount FROM deals WHERE id = ?', (deal_id,))
        row = cursor.fetchone()
        if not row or row['is_manual_amount']:
            return
        
        # Суммируем все line_total товаров
        cursor = conn.execute('''
            SELECT COALESCE(SUM(line_total), 0) as total
            FROM deal_products
            WHERE deal_id = ?
        ''', (deal_id,))
        row = cursor.fetchone()
        total = row['total'] if row else 0
        
        # Обновляем сумму сделки
        conn.execute('UPDATE deals SET amount = ? WHERE id = ?', (total, deal_id))
    
    def _log_history(
        self,
        conn,
        deal_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        change_type: str,
        user_id: int,
    ) -> None:
        """Логирует изменение в историю"""
        conn.execute('''
            INSERT INTO deal_history (deal_id, field_name, old_value, new_value, change_type, changed_by_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (deal_id, field_name, old_value, new_value, change_type, user_id))
    
    def _enrich_deal(self, conn, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Обогащает сделку связанными данными"""
        enriched = deal.copy()
        deal_id = deal['id']
        
        # Получаем воронку
        if deal.get('funnel_id'):
            cursor = conn.execute('SELECT id, name FROM funnels WHERE id = ?', (deal['funnel_id'],))
            row = cursor.fetchone()
            if row:
                enriched['funnel'] = dict(row)
        
        # Получаем стадию
        if deal.get('stage_id'):
            cursor = conn.execute('SELECT id, stage_id, name, label, order_index FROM deal_stages WHERE id = ?', (deal['stage_id'],))
            row = cursor.fetchone()
            if row:
                enriched['stage'] = dict(row)
        
        # Получаем компанию
        if deal.get('company_id'):
            cursor = conn.execute('SELECT id, name FROM customers WHERE id = ?', (deal['company_id'],))
            row = cursor.fetchone()
            if row:
                enriched['company'] = {'id': row['id'], 'name': row['name']}
        
        # Получаем основной контакт
        if deal.get('primary_contact_id'):
            cursor = conn.execute(
                'SELECT id, first_name, middle_name, last_name FROM contacts WHERE id = ?',
                (deal['primary_contact_id'],)
            )
            row = cursor.fetchone()
            if row:
                full_name = ' '.join(filter(None, [row['last_name'], row['first_name'], row['middle_name']])).strip()
                enriched['primary_contact'] = {'id': row['id'], 'name': full_name or row['first_name'] or ''}
        
        # Получаем ответственного пользователя
        if deal.get('responsible_user_id'):
            try:
                user = db_manager.get_user_by_id(deal['responsible_user_id'])
                if user:
                    enriched['responsible_user'] = {
                        'id': user['id'],
                        'name': user.get('full_name') or user.get('username', '')
                    }
            except Exception:
                pass
        
        # Получаем товары
        products_cursor = conn.execute(
            'SELECT * FROM deal_products WHERE deal_id = ? ORDER BY added_at ASC',
            (deal_id,)
        )
        enriched['products'] = [dict(row) for row in products_cursor.fetchall()]
        
        # Получаем файлы
        files_cursor = conn.execute('''
            SELECT * FROM deal_files
            WHERE deal_id = ? AND is_deleted = FALSE
            ORDER BY uploaded_at DESC
        ''', (deal_id,))
        enriched['files'] = [dict(row) for row in files_cursor.fetchall()]
        
        # Получаем комментарии
        comments_cursor = conn.execute('''
            SELECT dc.*, u.username as author_name, u.full_name as author_full_name
            FROM deal_comments dc
            LEFT JOIN users u ON dc.author_id = u.id
            WHERE dc.deal_id = ? AND dc.is_deleted = FALSE
            ORDER BY dc.created_at ASC
        ''', (deal_id,))
        comments = []
        for row in comments_cursor.fetchall():
            comment = dict(row)
            comment['author'] = {
                'id': comment.get('author_id'),
                'name': comment.get('author_full_name') or comment.get('author_name', '')
            }
            # Удаляем лишние поля
            comment.pop('author_name', None)
            comment.pop('author_full_name', None)
            comments.append(comment)
        enriched['comments'] = comments
        
        # Получаем участников
        participants_cursor = conn.execute('''
            SELECT dp.*, 
                   u.username AS user_name, 
                   u.full_name AS user_full_name,
                   c.first_name AS contact_first_name,
                   c.middle_name AS contact_middle_name,
                   c.last_name AS contact_last_name
            FROM deal_participants dp
            LEFT JOIN users u ON dp.user_id = u.id
            LEFT JOIN contacts c ON dp.contact_id = c.id
            WHERE dp.deal_id = ?
            ORDER BY dp.joined_at ASC
        ''', (deal_id,))
        participants = []
        for row in participants_cursor.fetchall():
            participant = dict(row)
            if participant.get('user_id'):
                participant['user'] = {
                    'id': participant.get('user_id'),
                    'name': participant.get('user_full_name') or participant.get('user_name', '')
                }
            if participant.get('contact_id'):
                full_name = ' '.join(
                    filter(
                        None,
                        [
                            participant.get('contact_last_name'),
                            participant.get('contact_first_name'),
                            participant.get('contact_middle_name'),
                        ],
                    )
                ).strip()
                participant['contact'] = {
                    'id': participant.get('contact_id'),
                    'name': full_name or participant.get('contact_first_name') or ''
                }
            participant.pop('user_name', None)
            participant.pop('user_full_name', None)
            participant.pop('contact_first_name', None)
            participant.pop('contact_middle_name', None)
            participant.pop('contact_last_name', None)
            participants.append(participant)
        enriched['participants'] = participants
        
        # Получаем историю
        history_cursor = conn.execute('''
            SELECT dh.*, u.username as changed_by_name, u.full_name as changed_by_full_name
            FROM deal_history dh
            LEFT JOIN users u ON dh.changed_by_id = u.id
            WHERE dh.deal_id = ?
            ORDER BY dh.changed_at DESC
        ''', (deal_id,))
        history = []
        for row in history_cursor.fetchall():
            h = dict(row)
            h['changed_by'] = {
                'id': h.get('changed_by_id'),
                'name': h.get('changed_by_full_name') or h.get('changed_by_name', '')
            }
            h.pop('changed_by_name', None)
            h.pop('changed_by_full_name', None)
            history.append(h)
        enriched['history'] = history
        
        return enriched


