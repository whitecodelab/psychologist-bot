from src.config.settings import settings

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == settings.ADMIN_IDS