"""
Сервис для работы с контактами (contacts) через SQLite
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..core.database import db_manager
from ..utils.storage import read_json_file, generate_external_id
from ..utils.validators import validate_email, validate_phone


CONTACTS_JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'contacts.json')


class ContactService:
    """Сервис для управления контактами на основе SQLite"""

    def __init__(self) -> None:
        self.json_path = CONTACTS_JSON_PATH
        self._legacy_migrated = False
        self._ensure_legacy_data_migrated()

    # ------------------------------------------------------------------
    # Legacy migration
    # ------------------------------------------------------------------
    def _ensure_legacy_data_migrated(self) -> None:
        if self._legacy_migrated:
            return
        self._legacy_migrated = True

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) AS cnt FROM contacts')
                if cursor.fetchone()['cnt'] > 0:
                    return
        except Exception:
            return

        legacy_contacts = read_json_file(self.json_path)
        if not legacy_contacts:
            return

        with db_manager.get_connection() as conn:
            for contact in legacy_contacts:
                self._insert_contact_from_legacy(conn, contact)
            conn.commit()

    def _insert_contact_from_legacy(self, conn, contact: Dict[str, Any]) -> int:
        first_name, middle_name, last_name = self._extract_names(contact)
        cursor = conn.execute(
            '''
            INSERT INTO contacts (
                external_id, first_name, middle_name, last_name, honorific,
                position, department, birthdate, photo_url, company_id,
                responsible_user_id, email, phone, is_active, deals_count,
                last_activity_at, created_at, updated_at, created_by_id, modified_by_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                contact.get('external_id'),
                first_name,
                middle_name,
                last_name,
                contact.get('honorific'),
                contact.get('position'),
                contact.get('department'),
                contact.get('birthdate'),
                contact.get('photo_url'),
                contact.get('company_id'),
                contact.get('responsible_user_id') or contact.get('responsible_id'),
                contact.get('email'),
                contact.get('phone'),
                contact.get('is_active', True),
                contact.get('deals_count', 0),
                contact.get('last_activity_at'),
                contact.get('created_at') or datetime.utcnow().isoformat(),
                contact.get('updated_at') or datetime.utcnow().isoformat(),
                contact.get('created_by_id'),
                contact.get('modified_by_id'),
            ),
        )
        contact_id = cursor.lastrowid
        external_id = contact.get('external_id') or generate_external_id('contact', contact_id)
        conn.execute('UPDATE contacts SET external_id = ? WHERE id = ?', (external_id, contact_id))

        for comm in contact.get('communications', []):
            conn.execute(
                '''
                INSERT INTO contact_communications (contact_id, comm_type, value_type, value, is_primary)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    contact_id,
                    comm.get('comm_type', 'PHONE'),
                    comm.get('value_type'),
                    comm.get('value', ''),
                    bool(comm.get('is_primary', False)),
                ),
            )

        for tag in contact.get('tags', []):
            conn.execute(
                '''
                INSERT OR IGNORE INTO contact_tags (contact_id, tag)
                VALUES (?, ?)
                ''',
                (contact_id, tag),
            )

        return contact_id

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _extract_names(self, data: Dict[str, Any]) -> Tuple[str, Optional[str], str]:
        first_name = (data.get('first_name') or '').strip()
        middle_name = (data.get('middle_name') or '').strip() or None
        last_name = (data.get('last_name') or '').strip()

        if not first_name and not last_name:
            name = (data.get('name') or '').strip()
            if name:
                parts = name.split()
                if len(parts) >= 2:
                    last_name = parts[0]
                    first_name = parts[1]
                    middle_name = ' '.join(parts[2:]) or None
                elif parts:
                    first_name = parts[0]
        return first_name, middle_name, last_name

    def _row_to_contact(self, row: Any) -> Dict[str, Any]:
        first_name = (row['first_name'] or '').strip() or 'Не указано'
        middle_name = (row['middle_name'] or '').strip() or ''
        last_name = (row['last_name'] or '').strip() or 'Не указано'
        display_name = ' '.join(filter(None, [last_name, first_name, middle_name])).strip() or first_name or last_name or 'Контакт'
        return {
            'id': row['id'],
            'external_id': row['external_id'],
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'name': display_name,
            'honorific': row['honorific'],
            'position': row['position'] or '',
            'department': row['department'] or '',
            'birthdate': row['birthdate'],
            'photo_url': row['photo_url'],
            'company_id': row['company_id'],
            'responsible_user_id': row['responsible_user_id'],
            'email': row['email'] or '',
            'phone': row['phone'] or '',
            'is_active': bool(row['is_active']),
            'deals_count': row['deals_count'] or 0,
            'last_activity_at': row['last_activity_at'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
        }

    def _fetch_communications(self, conn, contact_id: int) -> List[Dict[str, Any]]:
        cursor = conn.execute(
            '''
            SELECT id, comm_type, value_type, value, is_primary
            FROM contact_communications
            WHERE contact_id = ?
            ORDER BY is_primary DESC, id ASC
            ''',
            (contact_id,),
        )
        return [
            {
                'id': row['id'],
                'comm_type': row['comm_type'],
                'value_type': row['value_type'],
                'value': row['value'],
                'is_primary': bool(row['is_primary']),
            }
            for row in cursor.fetchall()
        ]

    def _fetch_tags(self, conn, contact_id: int) -> List[str]:
        cursor = conn.execute(
            '''
            SELECT tag
            FROM contact_tags
            WHERE contact_id = ?
            ORDER BY tag ASC
            ''',
            (contact_id,),
        )
        return [row['tag'] for row in cursor.fetchall()]

    def _attach_company_and_responsible(self, conn, contact: Dict[str, Any]) -> None:
        company_id = contact.get('company_id')
        if company_id:
            cursor = conn.execute('SELECT name FROM customers WHERE id = ?', (company_id,))
            row = cursor.fetchone()
            contact['company_name'] = row['name'] if row else ''
            contact['company'] = {'id': company_id, 'name': contact['company_name']} if row else None
        else:
            contact['company_name'] = ''
            contact['company'] = None

        responsible_id = contact.get('responsible_user_id')
        if responsible_id:
            cursor = conn.execute('SELECT full_name, username FROM users WHERE id = ?', (responsible_id,))
            row = cursor.fetchone()
            if row:
                contact['responsible_name'] = row['full_name'] or row['username'] or ''
                contact['responsible_user'] = {'id': responsible_id, 'name': contact['responsible_name']}
            else:
                contact['responsible_name'] = ''
                contact['responsible_user'] = None
        else:
            contact['responsible_name'] = ''
            contact['responsible_user'] = None

    def _hydrate_contact(self, conn, row: Any) -> Dict[str, Any]:
        contact = self._row_to_contact(row)
        contact['communications'] = self._fetch_communications(conn, row['id'])
        contact['tags'] = self._fetch_tags(conn, row['id'])
        self._attach_company_and_responsible(conn, contact)
        return contact

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        company_id: Optional[int] = None,
        responsible_user_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Список контактов с фильтрами"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            query = 'SELECT * FROM contacts WHERE 1=1'
            params: List[Any] = []

            if company_id is not None:
                query += ' AND company_id = ?'
                params.append(company_id)

            if responsible_user_id is not None:
                query += ' AND responsible_user_id = ?'
                params.append(responsible_user_id)

            if search:
                like = f"%{search.lower()}%"
                query += ' AND (LOWER(first_name) LIKE ? OR LOWER(last_name) LIKE ? OR LOWER(phone) LIKE ? OR LOWER(email) LIKE ?)'
                params.extend([like, like, like, like])

            if is_active is not None:
                query += ' AND is_active = ?'
                params.append(1 if is_active else 0)

            if tags:
                placeholders = ','.join('?' for _ in tags)
                query += f'''
                    AND EXISTS (
                        SELECT 1 FROM contact_tags ct
                        WHERE ct.contact_id = contacts.id
                        AND ct.tag IN ({placeholders})
                    )
                '''
                params.extend(tags)

            count_cursor = conn.execute(query.replace('SELECT *', 'SELECT COUNT(*) AS cnt'), params)
            total = count_cursor.fetchone()['cnt']

            query += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, skip])
            cursor = conn.execute(query, params)
            contacts = [self._hydrate_contact(conn, row) for row in cursor.fetchall()]
            return contacts, total

    def get_by_id(self, contact_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает контакт по ID"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._hydrate_contact(conn, row)

    def create(self, contact_data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """Создаёт контакт"""
        self._ensure_legacy_data_migrated()

        communications = contact_data.get('communications', []).copy()
        if not communications:
            if contact_data.get('email'):
                communications.append(
                    {
                        'comm_type': 'EMAIL',
                        'value_type': 'WORK',
                        'value': contact_data['email'],
                        'is_primary': True,
                    }
                )
            if contact_data.get('phone'):
                communications.append(
                    {
                        'comm_type': 'PHONE',
                        'value_type': 'WORK',
                        'value': contact_data['phone'],
                        'is_primary': not communications,
                    }
                )

        tags = contact_data.get('tags', []).copy()
        first_name, middle_name, last_name = self._extract_names(contact_data)
        email = contact_data.get('email')
        phone = contact_data.get('phone')

        if email and email.strip() and not validate_email(email):
            raise ValueError('Некорректный email')
        if phone and phone.strip() and not validate_phone(phone):
            raise ValueError('Некорректный телефон')

        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO contacts (
                    external_id, first_name, middle_name, last_name, honorific,
                    position, department, birthdate, photo_url, company_id,
                    responsible_user_id, email, phone, is_active, deals_count,
                    last_activity_at, created_at, updated_at, created_by_id, modified_by_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    None,
                    first_name,
                    middle_name,
                    last_name,
                    contact_data.get('honorific'),
                    contact_data.get('position'),
                    contact_data.get('department'),
                    contact_data.get('birthdate'),
                    contact_data.get('photo_url'),
                    contact_data.get('company_id'),
                    contact_data.get('responsible_user_id') or contact_data.get('responsible_id'),
                    email,
                    phone,
                    contact_data.get('is_active', True),
                    contact_data.get('deals_count', 0),
                    contact_data.get('last_activity_at'),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    user_id,
                    None,
                ),
            )
            contact_id = cursor.lastrowid
            external_id = generate_external_id('contact', contact_id)
            conn.execute('UPDATE contacts SET external_id = ? WHERE id = ?', (external_id, contact_id))

            for comm in communications:
                conn.execute(
                    '''
                    INSERT INTO contact_communications (contact_id, comm_type, value_type, value, is_primary)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        contact_id,
                        comm.get('comm_type', 'PHONE'),
                        comm.get('value_type'),
                        comm.get('value', ''),
                        bool(comm.get('is_primary', False)),
                    ),
                )

            for tag in tags:
                conn.execute(
                    '''
                    INSERT OR IGNORE INTO contact_tags (contact_id, tag)
                    VALUES (?, ?)
                    ''',
                    (contact_id, tag),
                )

            conn.commit()
            return self.get_by_id(contact_id)  # type: ignore[arg-type]

    def update(self, contact_id: int, contact_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Обновляет контакт"""
        self._ensure_legacy_data_migrated()

        email = contact_data.get('email')
        phone = contact_data.get('phone')
        if email and email.strip() and not validate_email(email):
            raise ValueError('Некорректный email')
        if phone and phone.strip() and not validate_phone(phone):
            raise ValueError('Некорректный телефон')
        if 'responsible_id' in contact_data and 'responsible_user_id' not in contact_data:
            contact_data['responsible_user_id'] = contact_data['responsible_id']

        fields_map = {
            'first_name': 'first_name',
            'middle_name': 'middle_name',
            'last_name': 'last_name',
            'honorific': 'honorific',
            'position': 'position',
            'department': 'department',
            'birthdate': 'birthdate',
            'photo_url': 'photo_url',
            'company_id': 'company_id',
            'responsible_user_id': 'responsible_user_id',
            'email': 'email',
            'phone': 'phone',
            'is_active': 'is_active',
            'last_activity_at': 'last_activity_at',
        }

        updates = []
        values: List[Any] = []

        if 'name' in contact_data:
            first_name, middle_name, last_name = self._extract_names(contact_data)
            contact_data.setdefault('first_name', first_name)
            contact_data.setdefault('middle_name', middle_name)
            contact_data.setdefault('last_name', last_name)

        for key, column in fields_map.items():
            if key in contact_data:
                updates.append(f"{column} = ?")
                values.append(contact_data[key])

        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            updates.append('modified_by_id = ?')
            values.append(user_id)
            values.append(contact_id)
            sql = f"UPDATE contacts SET {', '.join(updates)} WHERE id = ?"

            with db_manager.get_connection() as conn:
                cursor = conn.execute('SELECT id FROM contacts WHERE id = ?', (contact_id,))
                if not cursor.fetchone():
                    return None

                conn.execute(sql, values)

                if 'communications' in contact_data:
                    conn.execute('DELETE FROM contact_communications WHERE contact_id = ?', (contact_id,))
                    for comm in contact_data['communications'] or []:
                        conn.execute(
                            '''
                            INSERT INTO contact_communications (contact_id, comm_type, value_type, value, is_primary)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (
                                contact_id,
                                comm.get('comm_type', 'PHONE'),
                                comm.get('value_type'),
                                comm.get('value', ''),
                                bool(comm.get('is_primary', False)),
                            ),
                        )

                if 'tags' in contact_data:
                    conn.execute('DELETE FROM contact_tags WHERE contact_id = ?', (contact_id,))
                    for tag in contact_data['tags'] or []:
                        conn.execute(
                            '''
                            INSERT OR IGNORE INTO contact_tags (contact_id, tag)
                            VALUES (?, ?)
                            ''',
                            (contact_id, tag),
                        )

                conn.commit()

        return self.get_by_id(contact_id)

    def delete(self, contact_id: int) -> bool:
        """Удаляет контакт"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT id FROM contacts WHERE id = ?', (contact_id,))
            if not cursor.fetchone():
                return False
            conn.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
            conn.commit()
            return True

    # ------------------------------------------------------------------
    # Communications & tags
    # ------------------------------------------------------------------
    def add_communication(self, contact_id: int, communication: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Добавляет коммуникацию"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT id FROM contacts WHERE id = ?', (contact_id,))
            if not cursor.fetchone():
                return None

            if communication.get('is_primary'):
                conn.execute(
                    '''
                    UPDATE contact_communications
                    SET is_primary = FALSE
                    WHERE contact_id = ? AND comm_type = ?
                    ''',
                    (contact_id, communication.get('comm_type')),
                )

            conn.execute(
                '''
                INSERT INTO contact_communications (contact_id, comm_type, value_type, value, is_primary)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    contact_id,
                    communication.get('comm_type', 'PHONE'),
                    communication.get('value_type'),
                    communication.get('value', ''),
                    bool(communication.get('is_primary', False)),
                ),
            )
            conn.commit()
        return self.get_by_id(contact_id)

    def remove_communication(self, contact_id: int, comm_id: int) -> Optional[Dict[str, Any]]:
        """Удаляет коммуникацию"""
        self._ensure_legacy_data_migrated()
        with db_manager.get_connection() as conn:
            conn.execute(
                'DELETE FROM contact_communications WHERE id = ? AND contact_id = ?',
                (comm_id, contact_id),
            )
            conn.commit()
        return self.get_by_id(contact_id)

    def add_tag(self, contact_id: int, tag_name: str) -> Optional[Dict[str, Any]]:
        """Добавляет тег"""
        self._ensure_legacy_data_migrated()
        with db_manager.get_connection() as conn:
            conn.execute(
                '''
                INSERT OR IGNORE INTO contact_tags (contact_id, tag)
                VALUES (?, ?)
                ''',
                (contact_id, tag_name),
            )
            conn.commit()
        return self.get_by_id(contact_id)

    def remove_tag(self, contact_id: int, tag_name: str) -> Optional[Dict[str, Any]]:
        """Удаляет тег"""
        self._ensure_legacy_data_migrated()
        with db_manager.get_connection() as conn:
            conn.execute(
                'DELETE FROM contact_tags WHERE contact_id = ? AND tag = ?',
                (contact_id, tag_name),
            )
            conn.commit()
        return self.get_by_id(contact_id)

    # ------------------------------------------------------------------
    # Deal counters
    # ------------------------------------------------------------------
    def increment_deals_count(self, contact_id: int) -> None:
        with db_manager.get_connection() as conn:
            conn.execute(
                '''
                UPDATE contacts
                SET deals_count = deals_count + 1,
                    last_activity_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (contact_id,),
            )
            conn.commit()

    def decrement_deals_count(self, contact_id: int) -> None:
        with db_manager.get_connection() as conn:
            conn.execute(
                '''
                UPDATE contacts
                SET deals_count = CASE WHEN deals_count > 0 THEN deals_count - 1 ELSE 0 END
                WHERE id = ?
                ''',
                (contact_id,),
            )
            conn.commit()

