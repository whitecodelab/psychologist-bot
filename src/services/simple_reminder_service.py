import logging
from datetime import datetime
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


simple_reminder_service = SimpleReminderService()


def init_simple_reminder_service(bot: Bot):
    """Инициализирует простой сервис напоминаний"""
    simple_reminder_service.set_bot(bot)
    return simple_reminder_service