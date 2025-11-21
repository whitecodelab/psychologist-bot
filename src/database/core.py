import sqlite3
from contextlib import contextmanager
from .models import DatabaseManager
from src.config.settings import settings


db_manager = DatabaseManager(settings.DATABASE_URL)


@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с базой данных"""
    conn = db_manager.get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Инициализация базы данных"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for admin_id in settings.ADMIN_IDS:
            cursor.execute(
                'INSERT OR IGNORE INTO admins (telegram_id) VALUES (?)', 
                (admin_id,)
            )
            
        conn.commit()