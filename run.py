#!/usr/bin/env python3
"""
Точка входа в приложение Psychologist Bot
"""

import logging
from src.config.settings import settings
from src.bot.handlers.common_handlers import setup_handlers

def main():
    """Основная функция запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Валидация настроек
        settings.validate()
        logger.info("Настройки валидны, запуск бота...")
        
        # Запуск бота
        setup_handlers()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    main()