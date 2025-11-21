import sqlite3
from .core import get_db_connection

def book_appointment(slot_id: int, client_name: str, client_contact: str, client_request: str = "") -> bool:
    """
    Создает запись на консультацию
    Возвращает True если успешно, False если ошибка
    """
    print(f"🔍 DATABASE: Начало book_appointment, slot_id={slot_id}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Проверяем, что слот еще свободен
            cursor.execute(
                'SELECT id, datetime, is_booked FROM schedule_slots WHERE id = ?',
                (slot_id,)
            )
            slot = cursor.fetchone()
            
            print(f"🔍 DATABASE: Найден слот = {dict(slot) if slot else 'НЕ НАЙДЕН'}")
            
            if not slot:
                print(f"❌ DATABASE: Слот с ID {slot_id} не найден")
                return False
            
            if slot['is_booked']:
                print(f"❌ DATABASE: Слот с ID {slot_id} уже занят")
                return False
            
            print(f"🔍 DATABASE: Создаем запись для {client_name}")
            
            # Создаем запись
            cursor.execute(
                '''INSERT INTO appointments 
                (client_name, client_contact, client_request, slot_id) 
                VALUES (?, ?, ?, ?)''',
                (client_name, client_contact, client_request, slot_id)
            )
            
            # Помечаем слот как занятый
            cursor.execute(
                'UPDATE schedule_slots SET is_booked = TRUE WHERE id = ?',
                (slot_id,)
            )
            
            conn.commit()
            print(f"✅ DATABASE: Запись создана для {client_name} на слот {slot_id}")
            return True
            
    except Exception as e:
        print(f"❌ DATABASE: Ошибка при создании записи: {e}")
        import traceback
        print(f"❌ DATABASE: Подробности: {traceback.format_exc()}")
        return False

def get_appointments_for_admin():
    """Получает только будущие записи для админа"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    a.id as appointment_id,
                    a.client_name,
                    a.client_contact,
                    a.client_request,
                    s.datetime,
                    s.is_booked
                FROM appointments a
                JOIN schedule_slots s ON a.slot_id = s.id
                WHERE datetime(s.datetime) > datetime('now')  -- Только будущие записи
                ORDER BY s.datetime
            ''')
            
            appointments = cursor.fetchall()
            return [dict(appointment) for appointment in appointments]
            
    except Exception as e:
        print(f"❌ Ошибка при получении записей: {e}")
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
    
def get_past_appointments_for_admin():
    """Получает только прошедшие записи для админа"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    a.id as appointment_id,
                    a.client_name,
                    a.client_contact,
                    a.client_request,
                    s.datetime,
                    s.is_booked
                FROM appointments a
                JOIN schedule_slots s ON a.slot_id = s.id
                WHERE datetime(s.datetime) < datetime('now')  -- Только прошедшие записи
                ORDER BY s.datetime DESC
                LIMIT 20  -- Последние 20 записей
            ''')
            
            appointments = cursor.fetchall()
            return [dict(appointment) for appointment in appointments]
            
    except Exception as e:
        print(f"❌ Ошибка при получении архивных записей: {e}")
        return []
    
