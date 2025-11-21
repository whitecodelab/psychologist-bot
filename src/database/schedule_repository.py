import sqlite3
from .core import get_db_connection


def add_slot_to_schedule(datetime_str: str) -> bool:
    """Добавляет слот в расписание"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO schedule_slots (datetime, is_booked) VALUES (?, ?)',
                (datetime_str, False)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception:
        return False


def get_available_slots():
    """Получает все доступные слоты"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, datetime 
                FROM schedule_slots 
                WHERE is_booked = FALSE 
                ORDER BY datetime
            ''')
            slots = cursor.fetchall()
            return [dict(slot) for slot in slots]
    except Exception:
        return []


def delete_available_slot(slot_id: int) -> bool:
    """Удаляет свободный слот из расписания"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT id, is_booked FROM schedule_slots WHERE id = ?',
                (slot_id,)
            )
            slot = cursor.fetchone()
            
            if not slot or slot['is_booked']:
                return False
            
            cursor.execute('DELETE FROM schedule_slots WHERE id = ?', (slot_id,))
            conn.commit()
            return True
            
    except Exception:
        return False


def get_available_slots_for_deletion():
    """Получает будущие свободные слоты для удаления"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, datetime 
                FROM schedule_slots 
                WHERE is_booked = FALSE 
                AND datetime(datetime) > datetime('now')
                ORDER BY datetime
            ''')
            slots = cursor.fetchall()
            return [dict(slot) for slot in slots]
    except Exception:
        return []


def get_all_slots():
    """Получает все слоты"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, datetime, is_booked 
                FROM schedule_slots 
                ORDER BY datetime
            ''')
            slots = cursor.fetchall()
            return [dict(slot) for slot in slots]
    except Exception:
        return []


def get_future_slots():
    """Получает будущие слоты"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, datetime, is_booked 
                FROM schedule_slots 
                WHERE datetime(datetime) > datetime('now')
                ORDER BY datetime
            ''')
            slots = cursor.fetchall()
            return [dict(slot) for slot in slots]
    except Exception:
        return []