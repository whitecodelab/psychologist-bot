from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from src.config.settings import settings
from src.bot.keyboards.layouts import get_main_menu_keyboard, get_cancel_keyboard
from src.database.schedule_repository import get_available_slots
from src.database.appointment_repository import book_appointment
from src.utils.formatters import format_datetime
from src.services.working_reminder_service import working_reminder_service

# Состояния для ConversationHandler
(
    CHOOSING_SLOT, CHOOSING_TYPE, 
    TYPING_NAME, TYPING_CONTACT, 
    TYPING_THERAPY_EXPERIENCE, TYPING_DISORDERS,
    TYPING_REQUEST
) = range(7)


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
            
            keyboard = [
                [InlineKeyboardButton("🆕 Первичная консультация", callback_data="consult_type_primary")],
                [InlineKeyboardButton("🔄 Повторная консультация", callback_data="consult_type_repeat")],
                [InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")]
            ]
            
            await query.edit_message_text(
                f"✅ Вы выбрали время: **{format_datetime(selected_slot['datetime'])}**\n\n"
                "📋 **Выберите тип консультации:**",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return CHOOSING_TYPE
    
    await query.edit_message_text("❌ Произошла ошибка.")
    return ConversationHandler.END


async def client_choose_consultation_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа консультации"""
    query = update.callback_query
    await query.answer()
    
    consultation_type = query.data.replace("consult_type_", "")
    context.user_data['consultation_type'] = consultation_type
    
    if consultation_type == 'primary':
        await query.edit_message_text(
            "🆕 **Первичная консультация**\n\n"
            "Для первичной консультации нам нужно больше информации.\n\n"
            "Введите ваше **имя и фамилию**:",
            parse_mode='Markdown'
        )
        return TYPING_NAME
    else:
        await query.edit_message_text(
            "🔄 **Повторная консультация**\n\n"
            "Рады снова вас видеть!\n\n"
            "Введите ваше **имя и фамилию**:",
            parse_mode='Markdown'
        )
        return TYPING_NAME


async def client_input_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода имени клиента"""
    user_input = update.message.text.strip()
    
    if user_input == '❌ Отмена':
        await client_cancel_booking(update, context)
        return ConversationHandler.END
    
    if len(user_input) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Пожалуйста, введите ваше имя и фамилию:",
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_NAME
    
    context.user_data['client_name'] = user_input
    
    await update.message.reply_text(
        "📞 Теперь введите ваш **контакт для связи** (телефон или email):",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return TYPING_CONTACT


async def client_input_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода контакта клиента"""
    user_input = update.message.text.strip()
    
    if user_input == '❌ Отмена':
        await client_cancel_booking(update, context)
        return ConversationHandler.END
    
    if len(user_input) < 5:
        await update.message.reply_text(
            "❌ Контакт слишком короткий. Пожалуйста, введите телефон или email:",
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_CONTACT
    
    context.user_data['client_contact'] = user_input
    
    consultation_type = context.user_data.get('consultation_type', 'primary')
    
    if consultation_type == 'primary':
        await update.message.reply_text(
            "🧠 **Опыт работы с психологом:**\n\n"
            "Был ли у вас ранее опыт консультаций с психологом?\n"
            "Если да, опишите кратко:",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_THERAPY_EXPERIENCE
    else:
        await update.message.reply_text(
            "📝 **Необязательно:** Опишите кратко ваш запрос или проблему\n"
            "Или просто напишите 'Пропустить':",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_REQUEST


async def client_input_therapy_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода опыта с психологом (только для первичной)"""
    user_input = update.message.text.strip()
    
    if user_input == '❌ Отмена':
        await client_cancel_booking(update, context)
        return ConversationHandler.END
    
    context.user_data['therapy_experience'] = user_input
    
    await update.message.reply_text(
        "🏥 **Наличие расстройств или диагнозов:**\n\n"
        "Есть ли у вас официально поставленные диагнозы или расстройства?\n"
        "Если да, перечислите кратко (или напишите 'Нет'):",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return TYPING_DISORDERS


async def client_input_disorders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода информации о расстройствах (только для первичной)"""
    user_input = update.message.text.strip()
    
    if user_input == '❌ Отмена':
        await client_cancel_booking(update, context)
        return ConversationHandler.END
    
    context.user_data['disorders_info'] = user_input
    
    await update.message.reply_text(
        "📝 **Основной запрос:**\n\n"
        "Опишите кратко, с какой проблемой или вопросом вы хотели бы поработать:\n"
        "Или напишите 'Пропустить':",
        parse_mode='Markdown',
        reply_markup=get_cancel_keyboard()
    )
    return TYPING_REQUEST


async def client_input_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода запроса и завершение записи"""
    user_input = update.message.text.strip()
    
    if user_input == '❌ Отмена':
        await client_cancel_booking(update, context)
        return ConversationHandler.END
    
    if user_input.lower() == 'пропустить':
        user_input = "Не указано"
    
    selected_slot = context.user_data.get('selected_slot')
    client_name = context.user_data.get('client_name')
    client_contact = context.user_data.get('client_contact')
    consultation_type = context.user_data.get('consultation_type', 'primary')
    therapy_experience = context.user_data.get('therapy_experience', 'Не указано')
    disorders_info = context.user_data.get('disorders_info', 'Не указано')
    client_chat_id = update.effective_user.id
    
    if not all([selected_slot, client_name, client_contact]):
        await update.message.reply_text(
            "❌ Произошла ошибка. Не все данные заполнены.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return ConversationHandler.END
    
    if consultation_type == 'primary':
        full_request = (
            f"{user_input}\n\n"
            f"🧠 Опыт с психологом: {therapy_experience}\n"
            f"🏥 Диагнозы/расстройства: {disorders_info}"
        )
    else:
        full_request = user_input
    
    success = book_appointment(
        slot_id=selected_slot['id'],
        client_name=client_name,
        client_contact=client_contact,
        client_request=full_request,
        consultation_type=consultation_type
    )
    
    if success:
        try:
            await working_reminder_service.send_new_appointment_notification(
                client_name=client_name,
                appointment_datetime=selected_slot['datetime'],
                client_contact=client_contact,
                client_request=full_request
            )
            
            working_reminder_service.save_reminder_to_db(
                client_chat_id=client_chat_id,
                client_name=client_name,
                appointment_datetime=selected_slot['datetime']
            )
        except Exception:
            pass
        
        client_message = (
            "🎉 **Запись успешно оформлена!**\n\n"
            f"📅 **Время:** {format_datetime(selected_slot['datetime'])}\n"
            f"👤 **Имя:** {client_name}\n"
            f"📞 **Контакт:** {client_contact}\n"
            f"🎯 **Тип:** {'Первичная' if consultation_type == 'primary' else 'Повторная'} консультация\n"
            f"📝 **Запрос:** {full_request}\n\n"
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