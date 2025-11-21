from datetime import datetime


def format_datetime(datetime_str: str) -> str:
    """Форматирование даты для красивого отображения"""
    try:
        dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        return dt.strftime('%d.%m.%Y в %H:%M')
    except ValueError:
        return datetime_str