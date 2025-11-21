from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

def get_main_menu_keyboard(is_admin: bool = False):
    """Главное меню в зависимости от роли пользователя"""
    if is_admin:
        keyboard = [
            ['➕ Добавить слот', '🗑️ Удалить слот'],
            ['📋 Ближайшие записи', '👀 Мои слоты'],
            ['📚 Архив записей']  # <-- Новая кнопка
        ]
    else:
        keyboard = [['📅 Записаться на консультацию']]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_cancel_keyboard():
    """Клавиатура для отмены действия"""
    return ReplyKeyboardMarkup([['❌ Отмена']], resize_keyboard=True)