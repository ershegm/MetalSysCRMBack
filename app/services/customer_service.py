"""
Сервис для работы с клиентами (customers) через SQLite
"""
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..core.database import db_manager
from ..utils.customer_rules import CUSTOMER_TYPE_RULES, validate_customer_fields
from ..utils.storage import read_json_file, generate_external_id
from ..utils.validators import validate_inn, validate_kpp, validate_ogrn


CUSTOMERS_JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'customers.json')


class CustomerService:
    """Сервис для работы с клиентами на основе SQLite"""

    def __init__(self) -> None:
        self.json_path = CUSTOMERS_JSON_PATH
        self._legacy_migrated = False
        self._ensure_legacy_data_migrated()

    # ------------------------------------------------------------------
    # Legacy migration helpers
    # ------------------------------------------------------------------
    def _ensure_legacy_data_migrated(self) -> None:
        """Однократно переносит данные из legacy JSON в SQLite, если таблица пуста"""
        if self._legacy_migrated:
            return
        self._legacy_migrated = True

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute('SELECT COUNT(*) AS cnt FROM customers')
                if cursor.fetchone()['cnt'] > 0:
                    return
        except Exception:
            return

        legacy_customers = read_json_file(self.json_path)
        if not legacy_customers:
            return

        with db_manager.get_connection() as conn:
            for customer in legacy_customers:
                self._insert_customer_from_legacy(conn, customer)
            conn.commit()

    def _insert_customer_from_legacy(self, conn, customer: Dict[str, Any]) -> int:
        """Импортирует legacy запись клиента в SQLite"""
        customer_type = customer.get('customer_type', customer.get('type', 3)) or 3
        cursor = conn.execute(
            '''
            INSERT INTO customers (
                external_id, name, customer_type, email, phone, address_legal, address_real,
                inn, kpp, ogrn, agreement, manager_name, manager_post, notes,
                is_active, created_at, updated_at, currency_id, annual_revenue,
                employees_count, industry
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                customer.get('external_id'),
                customer.get('name', ''),
                int(customer_type),
                customer.get('email'),
                customer.get('phone'),
                customer.get('address_legal'),
                customer.get('address_real'),
                customer.get('inn'),
                customer.get('kpp'),
                customer.get('ogrn'),
                customer.get('agreement'),
                customer.get('manager_name'),
                customer.get('manager_post'),
                customer.get('notes'),
                customer.get('is_active', True),
                customer.get('created_at') or datetime.utcnow().isoformat(),
                customer.get('updated_at') or datetime.utcnow().isoformat(),
                customer.get('currency_id', 'RUB'),
                customer.get('annual_revenue'),
                customer.get('employees_count'),
                customer.get('industry'),
            ),
        )
        customer_id = cursor.lastrowid
        external_id = customer.get('external_id') or generate_external_id('customer', customer_id)
        conn.execute('UPDATE customers SET external_id = ? WHERE id = ?', (external_id, customer_id))

        for contact in customer.get('contacts', []):
            conn.execute(
                '''
                INSERT INTO customer_contacts (customer_id, contact_type, value_type, value, is_primary)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    customer_id,
                    contact.get('contact_type', 'PHONE'),
                    contact.get('value_type'),
                    contact.get('value', ''),
                    bool(contact.get('is_primary', False)),
                ),
            )

        for file_item in customer.get('files', []):
            conn.execute(
                '''
                INSERT INTO customer_files (
                    customer_id, file_name, file_path, file_type, file_size,
                    mime_type, version_number, is_deleted, uploaded_by_id, uploaded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    customer_id,
                    file_item.get('file_name', ''),
                    file_item.get('file_path'),
                    file_item.get('file_type', 'OTHER'),
                    file_item.get('file_size'),
                    file_item.get('mime_type'),
                    file_item.get('version_number', 1),
                    bool(file_item.get('is_deleted', False)),
                    file_item.get('uploaded_by_id'),
                    file_item.get('uploaded_at') or datetime.utcnow().isoformat(),
                ),
            )

        return customer_id

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------
    def _row_to_customer(self, row: Any) -> Dict[str, Any]:
        return {
            'id': row['id'],
            'external_id': row['external_id'],
            'name': row['name'],
            'customer_type': row['customer_type'],
            'type': row['customer_type'],
            'email': row['email'],
            'phone': row['phone'],
            'address_legal': row['address_legal'],
            'address_real': row['address_real'],
            'inn': row['inn'],
            'kpp': row['kpp'],
            'ogrn': row['ogrn'],
            'agreement': row['agreement'],
            'manager_name': row['manager_name'],
            'manager_post': row['manager_post'],
            'notes': row['notes'],
            'is_active': bool(row['is_active']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'created_by_id': row['created_by_id'],
            'modified_by_id': row['modified_by_id'],
            'currency_id': row['currency_id'],
            'annual_revenue': row['annual_revenue'],
            'employees_count': row['employees_count'],
            'industry': row['industry'],
        }

    def _fetch_customer_contacts(self, conn, customer_id: int) -> List[Dict[str, Any]]:
        cursor = conn.execute(
            '''
            SELECT id, contact_type, value_type, value, is_primary
            FROM customer_contacts
            WHERE customer_id = ?
            ORDER BY is_primary DESC, id ASC
            ''',
            (customer_id,),
        )
        return [
            {
                'id': row['id'],
                'contact_type': row['contact_type'],
                'value_type': row['value_type'],
                'value': row['value'],
                'is_primary': bool(row['is_primary']),
            }
            for row in cursor.fetchall()
        ]

    def _fetch_customer_files(self, conn, customer_id: int) -> List[Dict[str, Any]]:
        cursor = conn.execute(
            '''
            SELECT *
            FROM customer_files
            WHERE customer_id = ? AND is_deleted = FALSE
            ORDER BY uploaded_at DESC
            ''',
            (customer_id,),
        )
        return [
            {
                'id': row['id'],
                'file_name': row['file_name'],
                'file_path': row['file_path'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'mime_type': row['mime_type'],
                'version_number': row['version_number'],
                'uploaded_by_id': row['uploaded_by_id'],
                'uploaded_at': row['uploaded_at'],
            }
            for row in cursor.fetchall()
        ]

    def _hydrate_customer(self, conn, row: Any) -> Dict[str, Any]:
        customer = self._row_to_customer(row)
        customer['contacts'] = self._fetch_customer_contacts(conn, row['id'])
        customer['files'] = self._fetch_customer_files(conn, row['id'])
        return customer

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        customer_type: Optional[int] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Возвращает список клиентов с фильтрами"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            query = 'SELECT * FROM customers WHERE 1=1'
            params: List[Any] = []

            if customer_type is not None:
                query += ' AND customer_type = ?'
                params.append(customer_type)

            if search:
                query += ' AND (LOWER(name) LIKE ? OR inn LIKE ?)'
                like = f"%{search.lower()}%"
                params.extend([like, search])

            if is_active is not None:
                query += ' AND is_active = ?'
                params.append(1 if is_active else 0)

            count_cursor = conn.execute(
                query.replace('SELECT *', 'SELECT COUNT(*) AS cnt'),
                params,
            )
            total = count_cursor.fetchone()['cnt']

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, skip])
            cursor = conn.execute(query, params)
            customers = [self._hydrate_customer(conn, row) for row in cursor.fetchall()]
            return customers, total

    def get_by_id(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает клиента по ID"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._hydrate_customer(conn, row)

    def get_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """Возвращает клиента по ИНН"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM customers WHERE inn = ?', (inn.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            return self._hydrate_customer(conn, row)

    def create(self, customer_data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        """Создаёт клиента"""
        self._ensure_legacy_data_migrated()

        inn = customer_data.get('inn')
        if inn and inn.strip() and not validate_inn(inn):
            raise ValueError('Некорректный ИНН')
        kpp = customer_data.get('kpp')
        if kpp and kpp.strip() and not validate_kpp(kpp):
            raise ValueError('Некорректный КПП')
        ogrn = customer_data.get('ogrn')
        if ogrn and ogrn.strip() and not validate_ogrn(ogrn):
            raise ValueError('Некорректный ОГРН')

        customer_type = customer_data.get('customer_type', customer_data.get('type', 3)) or 3
        now = datetime.utcnow().isoformat()

        validate_customer_fields(int(customer_type), customer_data, allow_partial=False)

        contacts = customer_data.get('contacts') or []
        files = customer_data.get('files') or []

        if not contacts:
            if customer_data.get('email'):
                contacts.append(
                    {
                        'contact_type': 'EMAIL',
                        'value_type': 'WORK',
                        'value': customer_data['email'],
                        'is_primary': True,
                    }
                )
            if customer_data.get('phone'):
                contacts.append(
                    {
                        'contact_type': 'PHONE',
                        'value_type': 'WORK',
                        'value': customer_data['phone'],
                        'is_primary': not contacts,
                    }
                )

        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                '''
                INSERT INTO customers (
                    external_id, name, customer_type, email, phone, address_legal, address_real,
                    inn, kpp, ogrn, agreement, manager_name, manager_post, notes,
                    is_active, created_at, updated_at, created_by_id, modified_by_id,
                    currency_id, annual_revenue, employees_count, industry
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    None,
                    customer_data.get('name', ''),
                    int(customer_type),
                    customer_data.get('email'),
                    customer_data.get('phone'),
                    customer_data.get('address_legal'),
                    customer_data.get('address_real'),
                    inn,
                    kpp,
                    ogrn,
                    customer_data.get('agreement'),
                    customer_data.get('manager_name'),
                    customer_data.get('manager_post'),
                    customer_data.get('notes'),
                    customer_data.get('is_active', True),
                    now,
                    now,
                    user_id,
                    None,
                    customer_data.get('currency_id', 'RUB'),
                    customer_data.get('annual_revenue'),
                    customer_data.get('employees_count'),
                    customer_data.get('industry'),
                ),
            )
            customer_id = cursor.lastrowid
            external_id = generate_external_id('customer', customer_id)
            conn.execute('UPDATE customers SET external_id = ? WHERE id = ?', (external_id, customer_id))

            for contact in contacts:
                conn.execute(
                    '''
                    INSERT INTO customer_contacts (customer_id, contact_type, value_type, value, is_primary)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        customer_id,
                        contact.get('contact_type', 'PHONE'),
                        contact.get('value_type'),
                        contact.get('value', ''),
                        bool(contact.get('is_primary', False)),
                    ),
                )

            for file_item in files:
                conn.execute(
                    '''
                    INSERT INTO customer_files (
                        customer_id, file_name, file_path, file_type, file_size,
                        mime_type, version_number, uploaded_by_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        customer_id,
                        file_item.get('file_name', ''),
                        file_item.get('file_path'),
                        file_item.get('file_type', 'OTHER'),
                        file_item.get('file_size'),
                        file_item.get('mime_type'),
                        file_item.get('version_number', 1),
                        user_id,
                    ),
                )

            conn.commit()
            return self.get_by_id(customer_id)  # type: ignore[arg-type]

    def update(self, customer_id: int, customer_data: Dict[str, Any], user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Обновляет клиента"""
        self._ensure_legacy_data_migrated()

        inn = customer_data.get('inn')
        if inn and inn.strip() and not validate_inn(inn):
            raise ValueError('Некорректный ИНН')
        kpp = customer_data.get('kpp')
        if kpp and kpp.strip() and not validate_kpp(kpp):
            raise ValueError('Некорректный КПП')
        ogrn = customer_data.get('ogrn')
        if ogrn and ogrn.strip() and not validate_ogrn(ogrn):
            raise ValueError('Некорректный ОГРН')

        existing = self.get_by_id(customer_id)
        if not existing:
            return None

        target_type = int(customer_data.get('customer_type', existing.get('customer_type', 3)))

        # Собираем payload для валидации (заполняем отсутствующие значения текущими)
        validation_payload = {
            'customer_type': target_type,
            'inn': customer_data.get('inn', existing.get('inn', '')),
            'kpp': customer_data.get('kpp', existing.get('kpp', '')),
            'ogrn': customer_data.get('ogrn', existing.get('ogrn', '')),
            'email': customer_data.get('email', existing.get('email', '')),
            'phone': customer_data.get('phone', existing.get('phone', '')),
            'address_legal': customer_data.get('address_legal', existing.get('address_legal', '')),
            'address_real': customer_data.get('address_real', existing.get('address_real', '')),
        }
        validate_customer_fields(target_type, validation_payload, allow_partial=False)

        # Вносим очищенные поля обратно в payload обновления
        hidden_fields = set(CUSTOMER_TYPE_RULES.get(target_type, {}).get('hidden_fields', []))
        for field in ['inn', 'kpp', 'ogrn']:
            if field in customer_data or field in hidden_fields:
                customer_data[field] = validation_payload.get(field, '')

        fields_map = {
            'name': 'name',
            'customer_type': 'customer_type',
            'email': 'email',
            'phone': 'phone',
            'address_legal': 'address_legal',
            'address_real': 'address_real',
            'inn': 'inn',
            'kpp': 'kpp',
            'ogrn': 'ogrn',
            'agreement': 'agreement',
            'manager_name': 'manager_name',
            'manager_post': 'manager_post',
            'notes': 'notes',
            'is_active': 'is_active',
            'currency_id': 'currency_id',
            'annual_revenue': 'annual_revenue',
            'employees_count': 'employees_count',
            'industry': 'industry',
        }

        updates = []
        values: List[Any] = []
        for key, column in fields_map.items():
            if key in customer_data:
                updates.append(f"{column} = ?")
                values.append(customer_data[key])

        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            updates.append('modified_by_id = ?')
            values.append(user_id)
            values.append(customer_id)
            sql = f"UPDATE customers SET {', '.join(updates)} WHERE id = ?"

            with db_manager.get_connection() as conn:
                conn.execute(sql, values)

                if 'contacts' in customer_data:
                    conn.execute('DELETE FROM customer_contacts WHERE customer_id = ?', (customer_id,))
                    for contact in customer_data['contacts'] or []:
                        conn.execute(
                            '''
                            INSERT INTO customer_contacts (customer_id, contact_type, value_type, value, is_primary)
                            VALUES (?, ?, ?, ?, ?)
                            ''',
                            (
                                customer_id,
                                contact.get('contact_type', 'PHONE'),
                                contact.get('value_type'),
                                contact.get('value', ''),
                                bool(contact.get('is_primary', False)),
                            ),
                        )

                if 'files' in customer_data:
                    conn.execute('DELETE FROM customer_files WHERE customer_id = ?', (customer_id,))
                    for file_item in customer_data['files'] or []:
                        conn.execute(
                            '''
                            INSERT INTO customer_files (
                                customer_id, file_name, file_path, file_type, file_size,
                                mime_type, version_number, uploaded_by_id, is_deleted, uploaded_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''',
                            (
                                customer_id,
                                file_item.get('file_name', ''),
                                file_item.get('file_path'),
                                file_item.get('file_type', 'OTHER'),
                                file_item.get('file_size'),
                                file_item.get('mime_type'),
                                file_item.get('version_number', 1),
                                user_id,
                                bool(file_item.get('is_deleted', False)),
                                file_item.get('uploaded_at') or datetime.utcnow().isoformat(),
                            ),
                        )

                conn.commit()

        return self.get_by_id(customer_id)

    def delete(self, customer_id: int, soft: bool = True) -> bool:
        """Удаляет клиента"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT id FROM customers WHERE id = ?', (customer_id,))
            if not cursor.fetchone():
                return False

            if soft:
                conn.execute(
                    '''
                    UPDATE customers
                    SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    ''',
                    (customer_id,),
                )
            else:
                conn.execute('DELETE FROM customers WHERE id = ?', (customer_id,))

            conn.commit()
            return True

    # ------------------------------------------------------------------
    # Files
    # ------------------------------------------------------------------
    def add_file(
        self,
        customer_id: int,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: Optional[int],
        mime_type: Optional[str],
        user_id: Optional[int],
    ) -> Optional[Dict[str, Any]]:
        """Добавляет файл к клиенту с учётом версионирования"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute('SELECT id FROM customers WHERE id = ?', (customer_id,))
            if not cursor.fetchone():
                return None

            version_cursor = conn.execute(
                '''
                SELECT COALESCE(MAX(version_number), 0) AS max_version
                FROM customer_files
                WHERE customer_id = ? AND file_type = ? AND is_deleted = FALSE
                ''',
                (customer_id, file_type),
            )
            next_version = (version_cursor.fetchone()['max_version'] or 0) + 1

            cursor = conn.execute(
                '''
                INSERT INTO customer_files (
                    customer_id, file_name, file_path, file_type, file_size,
                    mime_type, version_number, uploaded_by_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    customer_id,
                    file_name,
                    file_path,
                    file_type,
                    file_size,
                    mime_type,
                    next_version,
                    user_id,
                ),
            )
            file_id = cursor.lastrowid
            conn.execute('UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (customer_id,))
            conn.commit()

            cursor = conn.execute('SELECT * FROM customer_files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                'id': row['id'],
                'file_name': row['file_name'],
                'file_path': row['file_path'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'mime_type': row['mime_type'],
                'version_number': row['version_number'],
                'uploaded_by_id': row['uploaded_by_id'],
                'uploaded_at': row['uploaded_at'],
            }

    def delete_file(self, customer_id: int, file_id: int) -> Optional[Dict[str, Any]]:
        """Помечает файл клиента как удалённый"""
        self._ensure_legacy_data_migrated()

        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                '''
                SELECT * FROM customer_files
                WHERE id = ? AND customer_id = ? AND is_deleted = FALSE
                ''',
                (file_id, customer_id),
            )
            row = cursor.fetchone()
            if not row:
                return None

            conn.execute(
                '''
                UPDATE customer_files
                SET is_deleted = TRUE
                WHERE id = ?
                ''',
                (file_id,),
            )
            conn.execute('UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (customer_id,))
            conn.commit()

            return {
                'id': row['id'],
                'file_name': row['file_name'],
                'file_path': row['file_path'],
                'file_type': row['file_type'],
                'file_size': row['file_size'],
                'mime_type': row['mime_type'],
                'version_number': row['version_number'],
                'uploaded_by_id': row['uploaded_by_id'],
                'uploaded_at': row['uploaded_at'],
                'is_deleted': True,
            }


