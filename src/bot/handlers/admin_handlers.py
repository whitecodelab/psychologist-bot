from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from src.config.settings import settings
from src.bot.keyboards.layouts import get_main_menu_keyboard, get_cancel_keyboard
from src.utils.validators import is_valid_datetime, is_future_datetime
from src.utils.formatters import format_datetime
from src.database.schedule_repository import get_available_slots, get_available_slots_for_deletion, delete_available_slot
from src.database.appointment_repository import get_appointments_for_admin
from telegram import ReplyKeyboardRemove


# Состояния для ConversationHandler
ADDING_SLOT = 1
DELETING_SLOT = 2

# ===== ДОБАВЛЕНИЕ СЛОТОВ =====
async def admin_add_slot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем, что это администратор
    if not settings.is_admin(user_id):  # <-- ИСПРАВЛЕНО
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📅 Введите дату и время для нового слота в формате:\n"
        "**ГГГГ-ММ-ДД ЧЧ:ММ**\n\n"
        "Например: `2025-11-25 14:00`\n"
        "Или нажмите ❌ Отмена для выхода.",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    
    return ADDING_SLOT

async def admin_add_slot_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенной даты и времени или отмены"""
    user_input = update.message.text.strip()
    
    print(f"🔍 DEBUG admin_add_slot_input: пользователь ввел '{user_input}'")
    
    # ПРОВЕРЯЕМ ОТМЕНУ ПЕРВЫМ ДЕЛОМ
    if user_input == '❌ Отмена':
        print("🔍 DEBUG: обнаружена отмена")
        await update.message.reply_text(
            "❌ Добавление слота отменено.",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    # Проверяем валидность формата даты
    if not is_valid_datetime(user_input):
        await update.message.reply_text(
            "❌ Неверный формат даты!\n"
            "Пожалуйста, введите в формате **ГГГГ-ММ-ДД ЧЧ:ММ**\n"
            "Например: `2025-11-25 14:00`\n"
            "Или нажмите ❌ Отмена для выхода.",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return ADDING_SLOT
    
    # Проверяем, что дата в будущем
    if not is_future_datetime(user_input):
        await update.message.reply_text(
            "❌ Нельзя добавлять прошедшие даты!\n"
            "Пожалуйста, введите дату в будущем.\n"
            "Или нажмите ❌ Отмена для выхода.",
            reply_markup=get_cancel_keyboard()
        )
        return ADDING_SLOT
    
    # Импортируем здесь чтобы избежать циклических импортов
    from src.database.schedule_repository import add_slot_to_schedule
    
    success = add_slot_to_schedule(user_input)
    
    if success:
        await update.message.reply_text(
            f"✅ Слот на {user_input} успешно добавлен в расписание!",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
    else:
        await update.message.reply_text(
            f"❌ Слот на {user_input} уже существует!",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
    
    return ConversationHandler.END

# ===== УДАЛЕНИЕ СЛОТОВ =====
async def admin_delete_slot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога удаления слотов с Reply-кнопками"""
    user_id = update.effective_user.id
    
    if not settings.is_admin(user_id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return ConversationHandler.END
    
    available_slots = get_available_slots_for_deletion()
    
    if not available_slots:
        await update.message.reply_text(
            "😔 Нет свободных слотов для удаления.",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    # Сохраняем слоты в context
    context.user_data['available_slots_for_deletion'] = available_slots
    
    # Создаем клавиатуру с слотами и отменой
    from src.bot.keyboards.layouts import get_slots_for_deletion_keyboard
    slots_keyboard = get_slots_for_deletion_keyboard(available_slots)
    
    await update.message.reply_text(
        "🗑️ **Удаление слотов**\n\n"
        "⚠️ Можно удалять только свободные слоты.\n"
        "👇 Выберите слот для удаления:",
        reply_markup=slots_keyboard,
        parse_mode='Markdown'
    )
    
    return DELETING_SLOT

async def admin_delete_slot_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора слота для удаления"""
    user_choice = update.message.text.strip()
    
    if user_choice == '❌ Отмена':
        await update.message.reply_text(
            "❌ Удаление отменено.",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    # Ищем выбранный слот
    available_slots = context.user_data.get('available_slots_for_deletion', [])
    selected_slot = None
    
    for slot in available_slots:
        formatted_date = format_datetime(slot['datetime'])
        if user_choice == formatted_date:
            selected_slot = slot
            break
    
    if selected_slot:
        # Удаляем слот
        success = delete_available_slot(selected_slot['id'])
        
        if success:
            await update.message.reply_text(
                f"✅ Слот **{format_datetime(selected_slot['datetime'])}** успешно удален!",
                reply_markup=get_main_menu_keyboard(is_admin=True),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                f"❌ Не удалось удалить слот **{format_datetime(selected_slot['datetime'])}**",
                reply_markup=get_main_menu_keyboard(is_admin=True),
                parse_mode='Markdown'
            )
    else:
        await update.message.reply_text(
            "❌ Слот не найден. Пожалуйста, выберите слот из списка.",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
    
    return ConversationHandler.END

# ===== ПРОСМОТР ЗАПИСЕЙ =====
async def admin_show_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает будущие записи для администратора"""
    user_id = update.effective_user.id
    
    if not settings.is_admin(user_id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return
    
    appointments = get_appointments_for_admin()
    
    if not appointments:
        message = (
            "📋 **Ближайшие записи**\n\n"
            "На данный момент нет предстоящих записей.\n"
            "Все будущие записи будут отображаться здесь."
        )
    else:
        from datetime import datetime
        current_time = datetime.now()
        
        message = "📋 **Ближайшие записи:**\n\n"
        for appointment in appointments:
            formatted_date = format_datetime(appointment['datetime'])
            
            # Определяем статус записи
            appointment_dt = datetime.strptime(appointment['datetime'], '%Y-%m-%d %H:%M')
            if appointment_dt > current_time:
                status = "🟢 Предстоящая"
            else:
                status = "🔴 Прошедшая"
            
            message += (
                f"👤 **{appointment['client_name']}**\n"
                f"📅 {formatted_date}\n"
                f"📞 {appointment['client_contact']}\n"
                f"📝 {appointment['client_request']}\n"
                f"🔄 {status}\n"
                f"――――――――――――――――――――\n"
            )
        
        message += f"\n📊 **Всего предстоящих записей:** {len(appointments)}"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога (для Reply-кнопок)"""
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )
    return ConversationHandler.END

async def admin_show_my_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает только будущие слоты администратора"""
    user_id = update.effective_user.id
    
    if not settings.is_admin(user_id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return
    
    # Получаем только будущие слоты из базы
    from src.database.schedule_repository import get_future_slots
    future_slots = get_future_slots()
    
    if not future_slots:
        message = (
            "👀 **Мои слоты**\n\n"
            "На данный момент нет активных слотов.\n"
            "Добавьте слоты через меню '➕ Добавить слот'"
        )
    else:
        message = "👀 **Мои активные слоты:**\n\n"
        
        free_slots = []
        booked_slots = []
        
        for slot in future_slots:
            formatted_date = format_datetime(slot['datetime'])
            if slot['is_booked']:
                booked_slots.append(f"• {formatted_date} 🔴 (Занят)")
            else:
                free_slots.append(f"• {formatted_date} 🟢 (Свободен)")
        
        if free_slots:
            message += "🟢 **Свободные слоты:**\n" + "\n".join(free_slots) + "\n\n"
        
        if booked_slots:
            message += "🔴 **Занятые слоты:**\n" + "\n".join(booked_slots)
        
        message += f"\n📊 **Итого:** {len(free_slots)} свободных, {len(booked_slots)} занятых"
        
        # Добавляем информацию о прошедших слотах
        from src.database.schedule_repository import get_all_slots
        from datetime import datetime
        
        all_slots = get_all_slots()
        current_time = datetime.now()
        past_slots = [slot for slot in all_slots if datetime.strptime(slot['datetime'], '%Y-%m-%d %H:%M') < current_time]
        
        if past_slots:
            message += f"\n\n📚 **В архиве:** {len(past_slots)} прошедших слотов"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )

async def admin_show_archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает архивные (прошедшие) записи"""
    user_id = update.effective_user.id
    
    if not settings.is_admin(user_id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return
    
    # Получаем прошедшие записи
    from src.database.appointment_repository import get_past_appointments_for_admin
    
    past_appointments = get_past_appointments_for_admin()
    
    if not past_appointments:
        message = (
            "📚 **Архив записей**\n\n"
            "Архивных записей пока нет.\n"
            "Здесь будут отображаться завершенные консультации."
        )
    else:
        message = "📚 **Архив записей (последние 20):**\n\n"
        for appointment in past_appointments:
            formatted_date = format_datetime(appointment['datetime'])
            
            message += (
                f"👤 **{appointment['client_name']}**\n"
                f"📅 {formatted_date}\n"
                f"📞 {appointment['client_contact']}\n"
                f"📝 {appointment['client_request']}\n"
                f"――――――――――――――――――――\n"
            )
        
        message += f"\n📊 **Всего в архиве:** {len(past_appointments)} записей"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )

