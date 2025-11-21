from datetime import datetime

def is_valid_datetime(datetime_str: str) -> bool:
    """Проверка валидности даты и времени"""
    try:
        datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

def is_future_datetime(datetime_str: str) -> bool:
    """Проверка, что дата в будущем"""
    try:
        target_dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        return target_dt > datetime.now()
    except ValueError:
        return False