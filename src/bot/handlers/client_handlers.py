from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from src.config.settings import settings
from src.bot.keyboards.layouts import get_main_menu_keyboard, get_cancel_keyboard
from src.database.schedule_repository import get_available_slots
from src.database.appointment_repository import book_appointment
from src.utils.formatters import format_datetime
from src.services.working_reminder_service import working_reminder_service

CHOOSING_SLOT, TYPING_NAME, TYPING_CONTACT, TYPING_REQUEST = range(4)


async def client_start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса записи для клиента"""
    available_slots = get_available_slots()
    
    if not available_slots:
        await update.message.reply_text(
            "😔 На данный момент нет свободных слотов для записи.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return ConversationHandler.END
    
    context.user_data['available_slots'] = available_slots
    
    keyboard = []
    for slot in available_slots:
        formatted_date = format_datetime(slot['datetime'])
        button = InlineKeyboardButton(formatted_date, callback_data=f"book_slot_{slot['id']}")
        keyboard.append([button])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")])
    
    await update.message.reply_text(
        "📅 **Выберите удобное время для консультации:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return CHOOSING_SLOT


async def client_choose_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора слота клиентом"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data

    if callback_data == "cancel_booking":
        await query.edit_message_text("❌ Запись отменена.")
        return ConversationHandler.END
    
    if callback_data.startswith("book_slot_"):
        slot_id = int(callback_data.replace("book_slot_", ""))
        
        selected_slot = None
        for slot in context.user_data['available_slots']:
            if slot['id'] == slot_id:
                selected_slot = slot
                break
        
        if selected_slot:
            context.user_data['selected_slot'] = selected_slot
            
            await query.edit_message_text(
                f"✅ Вы выбрали: **{format_datetime(selected_slot['datetime'])}**\n\n"
                "Теперь введите ваше **имя и фамилию**:",
                parse_mode='Markdown'
            )
            return TYPING_NAME
    
    await query.edit_message_text(
        "❌ Произошла ошибка. Пожалуйста, начните запись заново."
    )
    return ConversationHandler.END


async def client_input_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода имени клиента"""
    client_name = update.message.text.strip()
    
    if len(client_name) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Пожалуйста, введите ваше имя и фамилию:",
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_NAME
    
    context.user_data['client_name'] = client_name
    
    await update.message.reply_text(
        "📞 Теперь введите ваш **контакт для связи** (телефон или email):",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return TYPING_CONTACT


async def client_input_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода контакта клиента"""
    client_contact = update.message.text.strip()
    
    if len(client_contact) < 5:
        await update.message.reply_text(
            "❌ Контакт слишком короткий. Пожалуйста, введите телефон или email:",
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_CONTACT
    
    context.user_data['client_contact'] = client_contact
    
    await update.message.reply_text(
        "📝 **Необязательно:** Опишите кратко ваш запрос или проблему\n"
        "Или просто напишите 'Пропустить':",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return TYPING_REQUEST


async def client_input_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода запроса клиента и завершение записи"""
    client_request = update.message.text.strip()
    
    if client_request.lower() == 'пропустить':
        client_request = "Не указано"
    
    selected_slot = context.user_data.get('selected_slot')
    client_name = context.user_data.get('client_name')
    client_contact = context.user_data.get('client_contact')
    client_chat_id = update.effective_user.id
    
    if not all([selected_slot, client_name, client_contact]):
        await update.message.reply_text(
            "❌ Произошла ошибка. Не все данные заполнены.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return ConversationHandler.END
    
    success = book_appointment(
        slot_id=selected_slot['id'],
        client_name=client_name,
        client_contact=client_contact,
        client_request=client_request
    )
    
    if success:
        try:
            await working_reminder_service.send_new_appointment_notification(
                client_name=client_name,
                appointment_datetime=selected_slot['datetime'],
                client_contact=client_contact,
                client_request=client_request
            )
            
            working_reminder_service.save_reminder_to_db(
                client_chat_id=client_chat_id,
                client_name=client_name,
                appointment_datetime=selected_slot['datetime']
            )
        except Exception:
            pass  # Уведомления - дополнительная функция
        
        client_message = (
            "🎉 **Запись успешно оформлена!**\n\n"
            f"📅 **Время:** {format_datetime(selected_slot['datetime'])}\n"
            f"👤 **Имя:** {client_name}\n"
            f"📞 **Контакт:** {client_contact}\n"
            f"📝 **Запрос:** {client_request}\n\n"
            "🔔 **Вы получите напоминание за 24 часа до консультации.**"
        )
        
        await update.message.reply_text(
            client_message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при записи.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
    
    context.user_data.clear()
    return ConversationHandler.END


async def client_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена процесса записи клиентом"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Запись отменена.",
        reply_markup=get_main_menu_keyboard(is_admin=False)
    )
    return ConversationHandler.END