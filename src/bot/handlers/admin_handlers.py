from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.config.settings import settings
from src.bot.keyboards.layouts import get_main_menu_keyboard, get_cancel_keyboard
from src.utils.validators import is_valid_datetime, is_future_datetime
from src.utils.formatters import format_datetime
from src.database.schedule_repository import (
    get_available_slots_for_deletion, 
    delete_available_slot,
    add_slot_to_schedule,
    get_future_slots,
    get_all_slots
)
from src.database.appointment_repository import (
    get_appointments_for_admin,
    get_past_appointments_for_admin
)
from datetime import datetime

ADDING_SLOT, DELETING_SLOT = 1, 2


async def admin_add_slot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса добавления слота"""
    if not settings.is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📅 Введите дату и время для нового слота в формате:\n"
        "**ГГГГ-ММ-ДД ЧЧ:ММ**\n\n"
        "Например: `2025-11-25 14:00`",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return ADDING_SLOT


async def admin_add_slot_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка введенной даты и времени"""
    user_input = update.message.text.strip()
    
    if user_input == '❌ Отмена':
        await update.message.reply_text(
            "❌ Добавление слота отменено.",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    if not is_valid_datetime(user_input):
        await update.message.reply_text(
            "❌ Неверный формат даты!\n"
            "Пожалуйста, введите в формате **ГГГГ-ММ-ДД ЧЧ:ММ**",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return ADDING_SLOT
    
    if not is_future_datetime(user_input):
        await update.message.reply_text(
            "❌ Нельзя добавлять прошедшие даты!",
            reply_markup=get_cancel_keyboard()
        )
        return ADDING_SLOT
    
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


async def admin_delete_slot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса удаления слотов"""
    if not settings.is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return ConversationHandler.END
    
    available_slots = get_available_slots_for_deletion()
    
    if not available_slots:
        await update.message.reply_text(
            "😔 Нет свободных слотов для удаления.",
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        return ConversationHandler.END
    
    context.user_data['available_slots_for_deletion'] = available_slots
    
    from src.bot.keyboards.layouts import get_slots_for_deletion_keyboard
    
    await update.message.reply_text(
        "🗑️ **Удаление слотов**\n\n"
        "⚠️ Можно удалять только свободные слоты.",
        reply_markup=get_slots_for_deletion_keyboard(available_slots),
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
    
    available_slots = context.user_data.get('available_slots_for_deletion', [])
    selected_slot = None
    
    for slot in available_slots:
        if user_choice == format_datetime(slot['datetime']):
            selected_slot = slot
            break
    
    if selected_slot:
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


async def admin_show_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает будущие записи для администратора"""
    if not settings.is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return
    
    appointments = get_appointments_for_admin()
    
    if not appointments:
        message = "📋 **Ближайшие записи**\n\nНа данный момент нет предстоящих записей."
    else:
        current_time = datetime.now()
        message = "📋 **Ближайшие записи:**\n\n"
        
        for appointment in appointments:
            formatted_date = format_datetime(appointment['datetime'])
            appointment_dt = datetime.strptime(appointment['datetime'], '%Y-%m-%d %H:%M')
            status = "🟢 Предстоящая" if appointment_dt > current_time else "🔴 Прошедшая"
            
            message += (
                f"👤 **{appointment['client_name']}**\n"
                f"📅 {formatted_date}\n"
                f"📞 {appointment['client_contact']}\n"
                f"📝 {appointment['client_request']}\n"
                f"🎯 {'🆕 Первичная' if appointment.get('consultation_type') == 'primary' else '🔄 Повторная'}\n"
                f"🔄 {status}\n"
                f"――――――――――――――――――――\n"
            )
        
        message += f"\n📊 **Всего записей:** {len(appointments)}"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )


async def admin_show_my_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает слоты администратора"""
    if not settings.is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return
    
    future_slots = get_future_slots()
    
    if not future_slots:
        message = "👀 **Мои слоты**\n\nНа данный момент нет активных слотов."
    else:
        free_slots = []
        booked_slots = []
        
        for slot in future_slots:
            formatted_date = format_datetime(slot['datetime'])
            if slot['is_booked']:
                booked_slots.append(f"• {formatted_date} 🔴 (Занят)")
            else:
                free_slots.append(f"• {formatted_date} 🟢 (Свободен)")
        
        message = "👀 **Мои активные слоты:**\n\n"
        if free_slots:
            message += "🟢 **Свободные слоты:**\n" + "\n".join(free_slots) + "\n\n"
        if booked_slots:
            message += "🔴 **Занятые слоты:**\n" + "\n".join(booked_slots)
        
        message += f"\n📊 **Итого:** {len(free_slots)} свободных, {len(booked_slots)} занятых"
        
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
    """Показывает архивные записи"""
    if not settings.is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У вас нет прав для этой команды.")
        return
    
    past_appointments = get_past_appointments_for_admin()
    
    if not past_appointments:
        message = "📚 **Архив записей**\n\nАрхивных записей пока нет."
    else:
        message = "📚 **Архив записей:**\n\n"
        for appointment in past_appointments:
            formatted_date = format_datetime(appointment['datetime'])
            message += (
                f"👤 **{appointment['client_name']}**\n"
                f"📅 {formatted_date}\n"
                f"📞 {appointment['client_contact']}\n"
                f"📝 {appointment['client_request']}\n"
                f"🎯 {'🆕 Первичная' if appointment.get('consultation_type') == 'primary' else '🔄 Повторная'}\n"
                f"――――――――――――――――――――\n"
            )
        message += f"\n📊 **Всего в архиве:** {len(past_appointments)} записей"
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=get_main_menu_keyboard(is_admin=True)
    )
    return ConversationHandler.END