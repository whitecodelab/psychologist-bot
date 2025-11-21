from .core import get_db_connection


def book_appointment(slot_id: int, client_name: str, client_contact: str, client_request: str = "") -> bool:
    """Создает запись на консультацию"""
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
            
            cursor.execute(
                '''INSERT INTO appointments 
                (client_name, client_contact, client_request, slot_id) 
                VALUES (?, ?, ?, ?)''',
                (client_name, client_contact, client_request, slot_id)
            )
            
            cursor.execute(
                'UPDATE schedule_slots SET is_booked = TRUE WHERE id = ?',
                (slot_id,)
            )
            
            conn.commit()
            return True
            
    except Exception:
        return False


def get_appointments_for_admin():
    """Получает будущие записи для админа"""
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
                WHERE datetime(s.datetime) > datetime('now')
                ORDER BY s.datetime
            ''')
            
            appointments = cursor.fetchall()
            return [dict(appointment) for appointment in appointments]
            
    except Exception:
        return []


def get_past_appointments_for_admin():
    """Получает прошедшие записи для админа"""
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
                WHERE datetime(s.datetime) < datetime('now')
                ORDER BY s.datetime DESC
                LIMIT 20
            ''')
            
            appointments = cursor.fetchall()
            return [dict(appointment) for appointment in appointments]
            
    except Exception:
        return []