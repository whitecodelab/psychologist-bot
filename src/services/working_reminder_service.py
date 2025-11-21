import logging
from datetime import datetime, timedelta
from telegram import Bot
from src.config.settings import settings
from src.utils.formatters import format_datetime
from src.database.core import get_db_connection


class WorkingReminderService:
    def __init__(self):
        self.bot = None
        self.logger = logging.getLogger(__name__)

    def set_bot(self, bot: Bot):
        """Устанавливает бота для отправки сообщений"""
        self.bot = bot

    async def send_new_appointment_notification(self, client_name: str, appointment_datetime: str, 
                                              client_contact: str, client_request: str):
        """Отправляет уведомление админам о новой записи"""
        if not self.bot:
            return
            
        try:
            formatted_date = format_datetime(appointment_datetime)
            message = (
                f"🎉 **Новая запись на консультацию!**\n\n"
                f"👤 **Клиент:** {client_name}\n"
                f"📅 **Время:** {formatted_date}\n"
                f"📞 **Контакт:** {client_contact}\n"
                f"📝 **Запрос:** {client_request}"
            )
            
            for admin_id in settings.ADMIN_IDS:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
        except Exception:
            pass

    def save_reminder_to_db(self, client_chat_id: int, client_name: str, appointment_datetime: str):
        """Сохраняет напоминание в базу данных для отправки за 24 часа"""
        try:
            appointment_dt = datetime.strptime(appointment_datetime, '%Y-%m-%d %H:%M')
            reminder_time = appointment_dt - timedelta(hours=24)
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reminders 
                    (client_chat_id, client_name, appointment_datetime, reminder_time, is_sent) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (client_chat_id, client_name, appointment_datetime, reminder_time.isoformat(), False))
                conn.commit()
        except Exception:
            pass

    async def check_and_send_reminders(self):
        """Проверяет и отправляет напоминания, которые должны быть отправлены сейчас"""
        if not self.bot:
            return
            
        try:
            current_time = datetime.now()
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, client_chat_id, client_name, appointment_datetime 
                    FROM reminders 
                    WHERE reminder_time <= ? AND is_sent = FALSE
                ''', (current_time.isoformat(),))
                
                reminders = cursor.fetchall()
                
                for reminder in reminders:
                    reminder_id, client_chat_id, client_name, appointment_datetime = reminder
                    
                    await self._send_reminder_to_client(client_chat_id, client_name, appointment_datetime)
                    
                    cursor.execute('UPDATE reminders SET is_sent = TRUE WHERE id = ?', (reminder_id,))
                    conn.commit()
                    
        except Exception:
            pass

    async def _send_reminder_to_client(self, client_chat_id: int, client_name: str, appointment_datetime: str):
        """Отправляет напоминание клиенту"""
        try:
            formatted_date = format_datetime(appointment_datetime)
            message = (
                f"🔔 **Напоминание о консультации**\n\n"
                f"Привет, {client_name}!\n\n"
                f"Напоминаем, что завтра в **{formatted_date}** у вас запланирована консультация.\n\n"
                f"Пожалуйста, подготовьтесь к сессии."
            )
            
            await self.bot.send_message(
                chat_id=client_chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception:
            pass


working_reminder_service = WorkingReminderService()


def init_working_reminder_service(bot: Bot):
    """Инициализирует рабочий сервис напоминаний"""
    working_reminder_service.set_bot(bot)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_chat_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                appointment_datetime TEXT NOT NULL,
                reminder_time TEXT NOT NULL,
                is_sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    
    return working_reminder_service