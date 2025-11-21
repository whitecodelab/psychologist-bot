import sqlite3
from datetime import datetime
from .core import get_db_connection

def add_slot_to_schedule(datetime_str: str) -> bool:
    """
    Добавляет слот в расписание
    Возвращает True если успешно, False если слот уже существует
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Пытаемся добавить слот
            cursor.execute(
                'INSERT INTO schedule_slots (datetime, is_booked) VALUES (?, ?)',
                (datetime_str, False)
            )
            
            conn.commit()
            print(f"✅ Слот {datetime_str} добавлен в базу данных")
            return True
            
    except sqlite3.IntegrityError:
        # Ошибка уникальности - слот уже существует
        print(f"⚠️ Слот {datetime_str} уже существует")
        return False
    except Exception as e:
        print(f"❌ Ошибка при добавлении слота: {e}")
        return False

def get_available_slots():
    """Получает все доступные (незанятые) слоты"""
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
            
    except Exception as e:
        print(f"❌ Ошибка при получении слотов: {e}")
        return []

def get_slots_count():
    """Возвращает количество слотов в базе (для тестирования)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM schedule_slots')
            result = cursor.fetchone()
            return result['count'] if result else 0
    except Exception as e:
        print(f"❌ Ошибка при подсчете слотов: {e}")
        return 0
    
def get_schedule_statistics():
    """Получает статистику по расписанию"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Общее количество слотов
            cursor.execute('SELECT COUNT(*) as total FROM schedule_slots')
            total_slots = cursor.fetchone()['total']
            
            # Занятые слоты
            cursor.execute('SELECT COUNT(*) as booked FROM schedule_slots WHERE is_booked = TRUE')
            booked_slots = cursor.fetchone()['booked']
            
            # Свободные слоты
            cursor.execute('SELECT COUNT(*) as available FROM schedule_slots WHERE is_booked = FALSE')
            available_slots = cursor.fetchone()['available']
            
            # Записи на сегодня
            cursor.execute('''
                SELECT COUNT(*) as today 
                FROM appointments a 
                JOIN schedule_slots s ON a.slot_id = s.id 
                WHERE date(s.datetime) = date('now')
            ''')
            today_appointments = cursor.fetchone()['today']
            
            return {
                'total_slots': total_slots,
                'booked_slots': booked_slots,
                'available_slots': available_slots,
                'today_appointments': today_appointments
            }
            
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return None    
    
def delete_available_slot(slot_id: int) -> bool:
    """
    Удаляет свободный слот из расписания
    Возвращает True если успешно, False если ошибка или слот занят
    """
    print(f"🔍 DATABASE: удаление слота ID={slot_id}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, что слот существует и свободен
            cursor.execute(
                'SELECT id, is_booked FROM schedule_slots WHERE id = ?',
                (slot_id,)
            )
            slot = cursor.fetchone()
            
            print(f"🔍 DATABASE: найден слот = {dict(slot) if slot else 'НЕ НАЙДЕН'}")
            
            if not slot:
                print(f"❌ DATABASE: Слот с ID {slot_id} не найден")
                return False
            
            if slot['is_booked']:
                print(f"❌ DATABASE: Слот с ID {slot_id} занят, нельзя удалить")
                return False
            
            # Удаляем слот
            cursor.execute('DELETE FROM schedule_slots WHERE id = ?', (slot_id,))
            conn.commit()
            
            print(f"✅ DATABASE: Слот {slot_id} успешно удален")
            return True
            
    except Exception as e:
        print(f"❌ DATABASE: Ошибка при удалении слота: {e}")
        import traceback
        print(f"❌ DATABASE: Подробности: {traceback.format_exc()}")
        return False

def get_available_slots_for_deletion():
    """Получает только будущие свободные слоты для удаления"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, datetime 
                FROM schedule_slots 
                WHERE is_booked = FALSE 
                AND datetime(datetime) > datetime('now')  -- Только будущие слоты
                ORDER BY datetime
            ''')
            
            slots = cursor.fetchall()
            return [dict(slot) for slot in slots]
            
    except Exception as e:
        print(f"❌ Ошибка при получении слотов для удаления: {e}")
        return []
    
def get_all_slots():
    """Получает все слоты (и свободные, и занятые)"""
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
            
    except Exception as e:
        print(f"❌ Ошибка при получении всех слотов: {e}")
        return [] 


def get_todays_appointments():
    """Получает записи на сегодня (для напоминаний)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    a.client_name,
                    a.client_contact,
                    s.datetime
                FROM appointments a
                JOIN schedule_slots s ON a.slot_id = s.id
                WHERE date(s.datetime) = date('now')
                ORDER BY s.datetime
            ''')
            
            appointments = cursor.fetchall()
            return [dict(appointment) for appointment in appointments]
            
    except Exception as e:
        print(f"❌ Ошибка при получении сегодняшних записей: {e}")
        return []
    
def get_future_slots():
    """Получает только будущие слоты (и свободные, и занятые)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, datetime, is_booked 
                FROM schedule_slots 
                WHERE datetime(datetime) > datetime('now')  -- Только будущие слоты
                ORDER BY datetime
            ''')
            
            slots = cursor.fetchall()
            return [dict(slot) for slot in slots]
            
    except Exception as e:
        print(f"❌ Ошибка при получении будущих слотов: {e}")
        return []