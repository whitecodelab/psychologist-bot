import sqlite3


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url.replace('sqlite:///', '')
        self._init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с базой данных"""
        conn = sqlite3.connect(self.db_url)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Инициализация таблиц базы данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schedule_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datetime TEXT UNIQUE NOT NULL,
                    is_booked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    client_contact TEXT NOT NULL,
                    client_request TEXT,
                    slot_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (slot_id) REFERENCES schedule_slots (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()