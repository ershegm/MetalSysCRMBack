"""
Управление базой данных с репозиториями
"""
import sqlite3
import os
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any, List
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import bcrypt

from .config import settings
from .exceptions import AppException

# SQLAlchemy настройки
SQLALCHEMY_DATABASE_URL = settings.database_url

# Исправляем URL для SQLite
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # Убираем префикс sqlite:/// если он есть
    db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///", "")
    # Убираем префикс file: если он есть
    db_path = db_path.replace("file:", "")
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """Менеджер для работы с базой данных (legacy поддержка)"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'users.db')
        else:
            self.db_path = db_path
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Контекстный менеджер для работы с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise AppException(f"Ошибка базы данных: {str(e)}")
        finally:
            conn.close()
    
    def init_database(self):
        """Инициализация базы данных"""
        with self.get_connection() as conn:
            # Создаем таблицу пользователей
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login TEXT UNIQUE NOT NULL,
                    username TEXT NOT NULL,
                    full_name TEXT,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    role TEXT DEFAULT 'manager',
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Создаем таблицу предложений
            conn.execute('''
                CREATE TABLE IF NOT EXISTS proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    company TEXT DEFAULT '',
                    productType TEXT NOT NULL,
                    material TEXT NOT NULL,
                    materialGrade TEXT DEFAULT '',
                    dimensions TEXT NOT NULL,
                    selectedOperations TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Создаем админа по умолчанию, если его нет
            cursor = conn.execute('SELECT * FROM users WHERE login = ?', ('admin',))
            if not cursor.fetchone():
                import bcrypt
                password_hash = bcrypt.hashpw('admin'.encode('utf-8'), bcrypt.gensalt())
                conn.execute(
                    'INSERT INTO users (login, username, email, password_hash, is_admin) VALUES (?, ?, ?, ?, ?)',
                    ('admin', 'admin', 'admin@example.com', password_hash.decode('utf-8'), True)
                )
    
    def migrate_users_table(self):
        """Мигрирует таблицу users, добавляя новые поля"""
        with self.get_connection() as conn:
            # Проверяем структуру таблицы users
            cursor = conn.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Если нет новых колонок, пересоздаем таблицу
            if 'login' not in columns:
                print("Пересоздаем таблицу users с новыми полями...")
                
                # Создаем временную таблицу с новой структурой
                conn.execute('''
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        login TEXT UNIQUE NOT NULL,
                        username TEXT NOT NULL,
                        full_name TEXT,
                        email TEXT UNIQUE NOT NULL,
                        phone TEXT,
                        role TEXT DEFAULT 'manager',
                        password_hash TEXT NOT NULL,
                        is_admin BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Копируем данные из старой таблицы
                conn.execute('''
                    INSERT INTO users_new (id, login, username, full_name, email, phone, role, password_hash, is_admin, is_active, created_at)
                    SELECT id, 
                           CASE WHEN username = 'admin' THEN 'admin' ELSE username END,
                           username, 
                           COALESCE(full_name, ''), 
                           email, 
                           COALESCE(phone, ''), 
                           COALESCE(role, 'manager'), 
                           password_hash, 
                           is_admin, 
                           is_active, 
                           created_at
                    FROM users
                ''')
                
                # Удаляем старую таблицу
                conn.execute('DROP TABLE users')
                
                # Переименовываем новую таблицу
                conn.execute('ALTER TABLE users_new RENAME TO users')
                
                print("Таблица users успешно обновлена")
            else:
                print("Таблица users уже содержит новые поля")
                
            # Исправляем NULL значения в существующих записях
            conn.execute("UPDATE users SET full_name = '' WHERE full_name IS NULL")
            conn.execute("UPDATE users SET phone = '' WHERE phone IS NULL")
            conn.execute("UPDATE users SET role = 'manager' WHERE role IS NULL")
            print("Исправлены NULL значения в таблице users")
    
    def add_missing_columns(self):
        """Добавляет недостающие колонки в таблицу proposals"""
        with self.get_connection() as conn:
            # Проверяем структуру таблицы
            cursor = conn.execute("PRAGMA table_info(proposals)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Если таблица не имеет нужных колонок, пересоздаем её
            if 'productType' not in columns:
                conn.execute("DROP TABLE IF EXISTS proposals")
                conn.execute('''
                    CREATE TABLE proposals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        company TEXT DEFAULT '',
                        productType TEXT NOT NULL,
                        material TEXT NOT NULL,
                        materialGrade TEXT DEFAULT '',
                        dimensions TEXT NOT NULL,
                        selectedOperations TEXT NOT NULL,
                        result TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
            else:
                # Добавляем недостающие колонки по месту
                if 'company' not in columns:
                    try:
                        conn.execute("ALTER TABLE proposals ADD COLUMN company TEXT DEFAULT ''")
                    except Exception as e:
                        print(f"Ошибка добавления колонки company: {e}")
                
                # Добавляем колонки status и priority
                if 'status' not in columns:
                    try:
                        conn.execute("ALTER TABLE proposals ADD COLUMN status TEXT DEFAULT ''")
                    except Exception as e:
                        print(f"Ошибка добавления колонки status: {e}")
                
                if 'priority' not in columns:
                    try:
                        conn.execute("ALTER TABLE proposals ADD COLUMN priority TEXT DEFAULT ''")
                    except Exception as e:
                        print(f"Ошибка добавления колонки priority: {e}")
                
                if 'company' not in columns:
                    try:
                        conn.execute("ALTER TABLE proposals ADD COLUMN company TEXT DEFAULT ''")
                    except Exception as e:
                        print(f"Ошибка добавления колонки company: {e}")
    
    def get_user_by_login(self, login: str):
        """Получает пользователя по логину"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE login = ?', (login,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'login': row['login'],
                    'username': row['username'],
                    'email': row['email'],
                    'password_hash': row['password_hash'],
                    'is_admin': bool(row['is_admin'])
                }
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Возвращает список всех пользователей"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users ORDER BY created_at DESC')
            users: List[Dict[str, Any]] = []
            for row in cursor.fetchall():
                users.append({
                    'id': row['id'],
                    'login': row['login'] if 'login' in row.keys() else row['username'],  # fallback для старых записей
                    'username': row['username'],
                    'full_name': row['full_name'] if 'full_name' in row.keys() and row['full_name'] is not None else '',
                    'email': row['email'],
                    'phone': row['phone'] if 'phone' in row.keys() and row['phone'] is not None else '',
                    'role': row['role'] if 'role' in row.keys() and row['role'] is not None else 'manager',
                    'is_admin': bool(row['is_admin']),
                    'is_active': bool(row['is_active']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'] if 'updated_at' in row.keys() and row['updated_at'] is not None else ''
                })
            return users

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает пользователя по ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'login': row['login'] if 'login' in row.keys() else row['username'],
                    'username': row['username'],
                    'full_name': row['full_name'] if 'full_name' in row.keys() and row['full_name'] is not None else '',
                    'email': row['email'],
                    'phone': row['phone'] if 'phone' in row.keys() and row['phone'] is not None else '',
                    'role': row['role'] if 'role' in row.keys() and row['role'] is not None else 'manager',
                    'password_hash': row['password_hash'],
                    'is_admin': bool(row['is_admin']),
                    'is_active': bool(row['is_active']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'] if 'updated_at' in row.keys() and row['updated_at'] is not None else ''
                }
            return None

    def create_user(self, login: str, username: str, email: str, password: str, 
                   full_name: str = None, phone: str = None, role: str = 'manager', 
                   is_admin: bool = False) -> int:
        """Создает нового пользователя и возвращает его ID"""
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with self.get_connection() as conn:
            cursor = conn.execute(
                '''INSERT INTO users (login, username, full_name, email, phone, role, 
                   password_hash, is_admin, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (login, username, full_name, email, phone, role, password_hash, 
                 1 if is_admin else 0, 1)
            )
            conn.commit()
            return cursor.lastrowid

    def update_user(self, user_id: int, login: str = None, username: str = None, 
                   full_name: str = None, email: str = None, phone: str = None, 
                   role: str = None, is_admin: bool = None, is_active: bool = None) -> Dict[str, Any]:
        """Обновляет данные пользователя и возвращает обновленную запись"""
        with self.get_connection() as conn:
            # Строим динамический SQL запрос только для переданных полей
            set_clauses = []
            values = []
            
            if login is not None:
                set_clauses.append('login = ?')
                values.append(login)
            if username is not None:
                set_clauses.append('username = ?')
                values.append(username)
            if full_name is not None:
                set_clauses.append('full_name = ?')
                values.append(full_name)
            if email is not None:
                set_clauses.append('email = ?')
                values.append(email)
            if phone is not None:
                set_clauses.append('phone = ?')
                values.append(phone)
            if role is not None:
                set_clauses.append('role = ?')
                values.append(role)
            if is_admin is not None:
                set_clauses.append('is_admin = ?')
                values.append(1 if is_admin else 0)
            if is_active is not None:
                set_clauses.append('is_active = ?')
                values.append(1 if is_active else 0)
            
            if set_clauses:
                set_clauses.append('updated_at = CURRENT_TIMESTAMP')
                values.append(user_id)
                sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
                conn.execute(sql, values)
                conn.commit()
            
            cursor = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'login': row['login'] if 'login' in row.keys() else row['username'],
                    'username': row['username'],
                    'full_name': row['full_name'] if 'full_name' in row.keys() and row['full_name'] is not None else '',
                    'email': row['email'],
                    'phone': row['phone'] if 'phone' in row.keys() and row['phone'] is not None else '',
                    'role': row['role'] if 'role' in row.keys() and row['role'] is not None else 'manager',
                    'password_hash': row['password_hash'],
                    'is_admin': bool(row['is_admin']),
                    'is_active': bool(row['is_active']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'] if 'updated_at' in row.keys() and row['updated_at'] is not None else ''
                }
            return None

    def change_user_password(self, user_id: int, new_password: str) -> bool:
        """Меняет пароль пользователя"""
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with self.get_connection() as conn:
            cursor = conn.execute(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (new_hash, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def toggle_admin_status(self, user_id: int) -> Optional[bool]:
        """Инвертирует признак администратора и возвращает новое значение"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            new_value = 0 if row['is_admin'] else 1
            conn.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_value, user_id))
            conn.commit()
            return bool(new_value)

    def toggle_user_active_status(self, user_id: int) -> Optional[bool]:
        """Инвертирует признак активности и возвращает новое значение"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT is_active FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            new_value = 0 if row['is_active'] else 1
            conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_value, user_id))
            conn.commit()
            return bool(new_value)

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя, если он не администратор"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return False
            if row['is_admin']:
                return False
            cursor = conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_proposals(self, user_id: int = None):
        """Получает все предложения или предложения конкретного пользователя"""
        with self.get_connection() as conn:
            if user_id:
                cursor = conn.execute('SELECT * FROM proposals WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
            else:
                cursor = conn.execute('SELECT * FROM proposals ORDER BY created_at DESC')
            
            proposals = []
            for row in cursor.fetchall():
                proposal = {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'company': row['company'] if 'company' in row.keys() else '',
                    'productType': row['productType'],
                    'material': row['material'],
                    'materialGrade': row['materialGrade'],
                    'dimensions': row['dimensions'],
                    'selectedOperations': row['selectedOperations'],
                    'result': row['result'],
                    'created_at': row['created_at'],
                    'status': row['status'] if 'status' in row.keys() else '',
                    'priority': row['priority'] if 'priority' in row.keys() else ''
                }
                proposals.append(proposal)
            
            return proposals
    
    def get_proposal_by_id(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Получает одно предложение по ID"""
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM proposals WHERE id = ?', (proposal_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'company': row['company'] if 'company' in row.keys() else '',
                    'productType': row['productType'],
                    'material': row['material'],
                    'materialGrade': row['materialGrade'],
                    'dimensions': row['dimensions'],
                    'selectedOperations': row['selectedOperations'],
                    'result': row['result'],
                    'created_at': row['created_at'],
                    'status': row['status'] if 'status' in row.keys() else '',
                    'priority': row['priority'] if 'priority' in row.keys() else ''
                }
            return None

    def save_proposal(self, proposal_data: dict) -> int:
        """Сохраняет новое предложение в базу данных"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO proposals (
                    user_id, company, productType, material, materialGrade, 
                    dimensions, selectedOperations, result, status, priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                proposal_data.get('user_id'),
                proposal_data.get('company', ''),
                proposal_data.get('productType', ''),
                proposal_data.get('material', ''),
                proposal_data.get('materialGrade', ''),
                proposal_data.get('dimensions', ''),
                proposal_data.get('selectedOperations', ''),
                proposal_data.get('result', ''),
                proposal_data.get('status', ''),
                proposal_data.get('priority', '')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_proposal(self, proposal_id: int, proposal_data: dict) -> dict:
        """Обновляет предложение в базе данных"""
        with self.get_connection() as conn:
            # Строим динамический SQL запрос только для переданных полей
            if not proposal_data:
                return None
                
            set_clauses = []
            values = []
            
            for field, value in proposal_data.items():
                if field == 'company':
                    set_clauses.append('company = ?')
                    values.append(value)
                elif field == 'productType':
                    set_clauses.append('productType = ?')
                    values.append(value)
                elif field == 'material':
                    set_clauses.append('material = ?')
                    values.append(value)
                elif field == 'materialGrade':
                    set_clauses.append('materialGrade = ?')
                    values.append(value)
                elif field == 'dimensions':
                    set_clauses.append('dimensions = ?')
                    values.append(value)
                elif field == 'selectedOperations':
                    set_clauses.append('selectedOperations = ?')
                    values.append(value)
                elif field == 'result':
                    set_clauses.append('result = ?')
                    values.append(value)
                elif field == 'status':
                    set_clauses.append('status = ?')
                    values.append(value)
                elif field == 'priority':
                    set_clauses.append('priority = ?')
                    values.append(value)
            
            if not set_clauses:
                return None
                
            values.append(proposal_id)
            sql = f"UPDATE proposals SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor = conn.execute(sql, values)
            conn.commit()
            
            # Возвращаем обновленное предложение
            cursor = conn.execute('SELECT * FROM proposals WHERE id = ?', (proposal_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'company': row['company'] if 'company' in row.keys() else '',
                    'productType': row['productType'],
                    'material': row['material'],
                    'materialGrade': row['materialGrade'],
                    'dimensions': row['dimensions'],
                    'selectedOperations': row['selectedOperations'],
                    'result': row['result'],
                    'created_at': row['created_at'],
                    'status': row['status'] if 'status' in row.keys() else '',
                    'priority': row['priority'] if 'priority' in row.keys() else ''
                }
            return None
    
    def delete_proposal(self, proposal_id: int) -> bool:
        """Удаляет предложение из базы данных"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM proposals WHERE id = ?', (proposal_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def init_crm_tables(self):
        """Инициализация таблиц CRM (deals, funnels, stages и связанные таблицы)"""
        with self.get_connection() as conn:
            # Таблица клиентов (customers)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    name TEXT NOT NULL,
                    customer_type INTEGER NOT NULL DEFAULT 3,
                    email TEXT,
                    phone TEXT,
                    address_legal TEXT,
                    address_real TEXT,
                    inn TEXT,
                    kpp TEXT,
                    ogrn TEXT,
                    agreement TEXT,
                    manager_name TEXT,
                    manager_post TEXT,
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by_id INTEGER,
                    modified_by_id INTEGER,
                    currency_id TEXT DEFAULT 'RUB',
                    annual_revenue REAL,
                    employees_count INTEGER,
                    industry TEXT,
                    FOREIGN KEY (created_by_id) REFERENCES users(id),
                    FOREIGN KEY (modified_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица контактных данных клиентов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS customer_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    contact_type TEXT NOT NULL,
                    value_type TEXT,
                    value TEXT NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица файлов клиентов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS customer_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT,
                    file_type TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    version_number INTEGER DEFAULT 1,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    uploaded_by_id INTEGER,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица контактов (contacts)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    first_name TEXT,
                    middle_name TEXT,
                    last_name TEXT,
                    honorific TEXT,
                    position TEXT,
                    department TEXT,
                    birthdate DATE,
                    photo_url TEXT,
                    company_id INTEGER,
                    responsible_user_id INTEGER,
                    email TEXT,
                    phone TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    deals_count INTEGER DEFAULT 0,
                    last_activity_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by_id INTEGER,
                    modified_by_id INTEGER,
                    FOREIGN KEY (company_id) REFERENCES customers(id) ON DELETE SET NULL,
                    FOREIGN KEY (responsible_user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (modified_by_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Таблица коммуникаций контактов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contact_communications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    comm_type TEXT NOT NULL,
                    value_type TEXT,
                    value TEXT NOT NULL,
                    is_primary BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица тегов контактов
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contact_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                    UNIQUE(contact_id, tag)
                )
            ''')
            
            # Таблица воронок (funnels)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS funnels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_by_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (created_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица стадий воронок (deal_stages)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deal_stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    funnel_id INTEGER NOT NULL,
                    stage_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    label TEXT,
                    description TEXT,
                    color_text TEXT,
                    color_bg TEXT,
                    color_border TEXT,
                    order_index INTEGER NOT NULL DEFAULT 0,
                    is_system BOOLEAN DEFAULT FALSE,
                    stage_semantic_id TEXT DEFAULT 'P',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (funnel_id) REFERENCES funnels(id) ON DELETE CASCADE,
                    UNIQUE(funnel_id, stage_id),
                    UNIQUE(funnel_id, order_index)
                )
            ''')
            
            # Таблица метрик по стадиям (stage_metrics)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS stage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage_id INTEGER NOT NULL,
                    deals_count INTEGER DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    avg_days_in_stage REAL DEFAULT 0,
                    conversion_percent REAL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stage_id) REFERENCES deal_stages(id) ON DELETE CASCADE,
                    UNIQUE(stage_id)
                )
            ''')
            
            # Таблица сделок (deals)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id TEXT UNIQUE,
                    deal_number TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    deal_type TEXT NOT NULL DEFAULT 'SALE',
                    funnel_id INTEGER NOT NULL,
                    stage_id INTEGER NOT NULL,
                    amount REAL NOT NULL DEFAULT 0,
                    currency_id TEXT DEFAULT 'RUB',
                    probability_percent INTEGER DEFAULT 50,
                    is_manual_amount BOOLEAN DEFAULT FALSE,
                    tax_value REAL DEFAULT 0,
                    start_date DATE,
                    close_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    company_id INTEGER,
                    responsible_user_id INTEGER NOT NULL,
                    primary_contact_id INTEGER,
                    is_closed BOOLEAN DEFAULT FALSE,
                    is_public BOOLEAN DEFAULT TRUE,
                    is_new BOOLEAN DEFAULT TRUE,
                    is_recurring BOOLEAN DEFAULT FALSE,
                    recurrence_pattern TEXT,
                    is_return_customer BOOLEAN DEFAULT FALSE,
                    source_id TEXT,
                    source_description TEXT,
                    utm_source TEXT,
                    utm_medium TEXT,
                    utm_campaign TEXT,
                    utm_content TEXT,
                    utm_term TEXT,
                    created_by_id INTEGER,
                    modified_by_id INTEGER,
                    moved_by_id INTEGER,
                    moved_at TIMESTAMP,
                    last_activity_at TIMESTAMP,
                    last_activity_by_id INTEGER,
                    originator_id TEXT,
                    origin_id TEXT,
                    FOREIGN KEY (funnel_id) REFERENCES funnels(id),
                    FOREIGN KEY (stage_id) REFERENCES deal_stages(id),
                    FOREIGN KEY (company_id) REFERENCES customers(id) ON DELETE SET NULL,
                    FOREIGN KEY (responsible_user_id) REFERENCES users(id),
                    FOREIGN KEY (created_by_id) REFERENCES users(id),
                    FOREIGN KEY (modified_by_id) REFERENCES users(id),
                    FOREIGN KEY (moved_by_id) REFERENCES users(id),
                    FOREIGN KEY (last_activity_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица товаров в сделках (deal_products)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deal_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER NOT NULL,
                    product_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL DEFAULT 1,
                    unit TEXT,
                    discount_percent REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    line_total REAL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_by_id INTEGER,
                    FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE,
                    FOREIGN KEY (added_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица файлов сделок (deal_files) с версионированием
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deal_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    version_number INTEGER DEFAULT 1,
                    is_current BOOLEAN DEFAULT TRUE,
                    parent_version_id INTEGER,
                    uploaded_by_id INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_version_id) REFERENCES deal_files(id),
                    FOREIGN KEY (uploaded_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица комментариев к сделкам (deal_comments)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deal_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER NOT NULL,
                    author_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    formatted_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    parent_comment_id INTEGER,
                    FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES users(id),
                    FOREIGN KEY (parent_comment_id) REFERENCES deal_comments(id) ON DELETE CASCADE
                )
            ''')
            
            # Таблица истории изменений сделок (deal_history)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deal_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    change_type TEXT NOT NULL,
                    changed_by_id INTEGER NOT NULL,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE,
                    FOREIGN KEY (changed_by_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица участников сделок (deal_participants)
            # Примечание: SQLite не поддерживает выражения в UNIQUE constraints
            # Проверка уникальности будет на уровне приложения
            conn.execute('''
                CREATE TABLE IF NOT EXISTS deal_participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER NOT NULL,
                    contact_id INTEGER,
                    user_id INTEGER,
                    participant_type TEXT NOT NULL,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals(id) ON DELETE CASCADE,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # Создаём индекс для быстрого поиска участников сделки
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_participants_deal_contact ON deal_participants(deal_id, contact_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_participants_deal_user ON deal_participants(deal_id, user_id)')
            
            # Создание индексов для производительности
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_funnel_id ON deals(funnel_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_stage_id ON deals(stage_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_company_id ON deals(company_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_responsible_user_id ON deals(responsible_user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_close_date ON deals(close_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_is_closed ON deals(is_closed)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deals_external_id ON deals(external_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_products_deal_id ON deal_products(deal_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_files_deal_id ON deal_files(deal_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_files_file_type ON deal_files(file_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_files_uploaded_at ON deal_files(uploaded_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_comments_deal_id ON deal_comments(deal_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_comments_author_id ON deal_comments(author_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_comments_created_at ON deal_comments(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_history_deal_id ON deal_history(deal_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_history_changed_at ON deal_history(changed_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_history_field_name ON deal_history(field_name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_participants_deal_id ON deal_participants(deal_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_stages_funnel_id ON deal_stages(funnel_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_deal_stages_order_index ON deal_stages(order_index)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_funnels_is_default ON funnels(is_default)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customers_inn ON customers(inn)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customers_type ON customers(customer_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customers_is_active ON customers(is_active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customer_contacts_customer_id ON customer_contacts(customer_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_customer_files_customer_id ON customer_files(customer_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_company_id ON contacts(company_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_responsible_user_id ON contacts(responsible_user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contacts_is_active ON contacts(is_active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contact_communications_contact_id ON contact_communications(contact_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contact_tags_contact_id ON contact_tags(contact_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_contact_tags_tag ON contact_tags(tag)')
            
            conn.commit()


# Глобальный экземпляр для legacy поддержки
db_manager = DatabaseManager()

