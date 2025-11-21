from telegram import ReplyKeyboardMarkup
from src.utils.formatters import format_datetime


def get_main_menu_keyboard(is_admin: bool = False):
    """Главное меню в зависимости от роли пользователя"""
    if is_admin:
        keyboard = [
            ['➕ Добавить слот', '🗑️ Удалить слот'],
            ['📋 Ближайшие записи', '👀 Мои слоты'],
            ['📚 Архив записей']
        ]
    else:
        keyboard = [['📅 Записаться на консультацию']]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_cancel_keyboard():
    """Клавиатура для отмены действия"""
    return ReplyKeyboardMarkup([['❌ Отмена']], resize_keyboard=True)


def get_slots_for_deletion_keyboard(available_slots):
    """Клавиатура с слотами для удаления"""
    keyboard = []
    
    for slot in available_slots:
        formatted_date = format_datetime(slot['datetime'])
        keyboard.append([formatted_date])
    
    keyboard.append(['❌ Отмена'])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)