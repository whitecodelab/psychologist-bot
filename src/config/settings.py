import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Администраторы (можно указать несколько ID через запятую)
    ADMIN_IDS = []
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./psychologist_bot.db')
    
    # Bot settings
    REMINDER_HOURS_BEFORE = 24  # За сколько часов напоминать
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        print(f"🔍 DEBUG is_admin: user_id={user_id}, ADMIN_IDS={cls.ADMIN_IDS}")
        result = user_id in cls.ADMIN_IDS
        print(f"🔍 DEBUG is_admin: результат={result}")
        return result
    
    @classmethod
    def validate(cls):
        """Проверка обязательных настроек"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        
        # Загружаем ADMIN_IDS из .env
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        if admin_ids_str:
            try:
                cls.ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
                print(f"✅ Загружены ADMIN_IDS: {cls.ADMIN_IDS}")
            except ValueError as e:
                raise ValueError(f"Ошибка в формате ADMIN_IDS: {e}")
        
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS не установлены в .env файле")

# Глобальный экземпляр настроек
settings = Settings()