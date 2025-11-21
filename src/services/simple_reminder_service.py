import logging
from datetime import datetime, timedelta
from telegram import Bot
from src.config.settings import settings
from src.utils.formatters import format_datetime

class SimpleReminderService:
    def __init__(self):
        self.bot = None
        self.logger = logging.getLogger(__name__)

    def set_bot(self, bot: Bot):
        """Устанавливает бота для отправки сообщений"""
        self.bot = bot

    async def send_new_appointment_notification(self, client_name: str, appointment_datetime: str, client_contact: str, client_request: str):
        """Отправляет уведомление админам о новой записи"""
        if not self.bot:
            print("❌ Бот не установлен в сервисе уведомлений")
            return
            
        try:
            formatted_date = format_datetime(appointment_datetime)
            message = (
                f"🎉 **Новая запись на консультацию!**\n\n"
                f"👤 **Клиент:** {client_name}\n"
                f"📅 **Время:** {formatted_date}\n"
                f"📞 **Контакт:** {client_contact}\n"
                f"📝 **Запрос:** {client_request}\n\n"
                f"Не забудьте подготовиться к сессии!"
            )
            
            # Отправляем всем админам
            for admin_id in settings.ADMIN_IDS:
                await self.bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode='Markdown'
                )
            
            print(f"✅ Уведомление о новой записи отправлено админам")
            
        except Exception as e:
            print(f"❌ Ошибка отправки уведомления о новой записи: {e}")

    async def send_test_reminder(self, client_chat_id: int, client_name: str, appointment_datetime: str):
        """Отправляет тестовое напоминание (для демонстрации)"""
        if not self.bot:
            print("❌ Бот не установлен в сервисе уведомлений")
            return
            
        try:
            formatted_date = format_datetime(appointment_datetime)
            message = (
                f"🔔 **Тестовое напоминание о консультации**\n\n"
                f"Привет, {client_name}!\n\n"
                f"Это тестовое напоминание о вашей консультации **{formatted_date}**.\n\n"
                f"В реальной системе это напоминание пришло бы за 24 часа до консультации."
            )
            
            await self.bot.send_message(
                chat_id=client_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            print(f"✅ Тестовое напоминание отправлено клиенту {client_name}")
            
        except Exception as e:
            print(f"❌ Ошибка отправки тестового напоминания: {e}")

# Глобальный экземпляр
simple_reminder_service = SimpleReminderService()

def init_simple_reminder_service(bot: Bot):
    """Инициализирует простой сервис напоминаний"""
    simple_reminder_service.set_bot(bot)
    print("✅ Простой сервис напоминаний инициализирован")
    return simple_reminder_service