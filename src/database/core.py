import sqlite3
from contextlib import contextmanager
from .models import DatabaseManager
from src.config.settings import settings

# Инициализация базы данных при импорте
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
    """Инициализация базы данных с тестовыми данными"""
    # Добавляем всех администраторов из настроек
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for admin_idS in settings.ADMIN_IDS:  # <-- ИСПРАВИЛИ ЗДЕСЬ
            cursor.execute(
                'INSERT OR IGNORE INTO admins (telegram_id) VALUES (?)', 
                (admin_idS,)
            )
            print(f"✅ Добавлен администратор: {admin_idS}")
            
        conn.commit()
    print("✅ База данных инициализирована")