import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Конфигурация приложения"""
    
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_IDS = []
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./psychologist_bot.db')
    REMINDER_HOURS_BEFORE = 24
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in cls.ADMIN_IDS
    
    @classmethod
    def validate(cls):
        """Проверка обязательных настроек"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            try:
                cls.ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
            except ValueError as e:
                raise ValueError(f"Ошибка в формате ADMIN_IDS: {e}")
        
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS не установлены в .env файле")


settings = Settings()