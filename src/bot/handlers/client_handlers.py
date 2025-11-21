from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from src.config.settings import settings
from src.bot.keyboards.layouts import get_main_menu_keyboard, get_cancel_keyboard
from src.database.schedule_repository import get_available_slots
from src.database.appointment_repository import book_appointment
from src.utils.formatters import format_datetime
from src.services.working_reminder_service import working_reminder_service


# Состояния для ConversationHandler (процесс записи клиента)
CHOOSING_SLOT, TYPING_NAME, TYPING_CONTACT, TYPING_REQUEST = range(4)

async def client_start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса записи для клиента"""
    print(f"🔍 DEBUG client_start_booking: пользователь {update.effective_user.id} начал запись")
    
    # Получаем доступные слоты из базы
    available_slots = get_available_slots()
    print(f"🔍 DEBUG: найдено слотов: {len(available_slots)}")
    
    if not available_slots:
        await update.message.reply_text(
            "😔 На данный момент нет свободных слотов для записи.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с администратором.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return ConversationHandler.END
    
    # Сохраняем слоты в context для последующего использования
    context.user_data['available_slots'] = available_slots
    
    # Создаем клавиатуру с доступными слотами
    keyboard = []
    for slot in available_slots:
        formatted_date = format_datetime(slot['datetime'])
        button = InlineKeyboardButton(formatted_date, callback_data=f"book_slot_{slot['id']}")
        keyboard.append([button])
        print(f"🔍 DEBUG: добавлен слот {slot['id']} - {formatted_date}")
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_booking")])
    
    await update.message.reply_text(
        "📅 **Выберите удобное время для консультации:**\n\n"
        "Доступные слоты:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return CHOOSING_SLOT

async def client_choose_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора слота клиентом"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    print(f"🔍 DEBUG client_choose_slot: callback_data = {callback_data}")

    if callback_data == "cancel_booking":
        await query.edit_message_text(
            "❌ Запись отменена.",
            reply_markup=None  # Убираем клавиатуру при отмене
        )
        return ConversationHandler.END
    
    if callback_data.startswith("book_slot_"):
        slot_id = int(callback_data.replace("book_slot_", ""))
        print(f"🔍 DEBUG: выбран slot_id = {slot_id}")
        
        # Находим выбранный слот
        selected_slot = None
        for slot in context.user_data['available_slots']:
            if slot['id'] == slot_id:
                selected_slot = slot
                break
        
        if selected_slot:
            # Сохраняем выбранный слот в context
            context.user_data['selected_slot'] = selected_slot
            
            # Убираем инлайн-клавиатуру и переходим к следующему шагу
            await query.edit_message_text(
                f"✅ Вы выбрали: **{format_datetime(selected_slot['datetime'])}**\n\n"
                "Теперь введите ваше **имя и фамилию**:",
                parse_mode='Markdown'
            )
            
            return TYPING_NAME
        else:
            print(f"❌ DEBUG: слот с ID {slot_id} не найден в available_slots")
    
    # Если что-то пошло не так
    await query.edit_message_text(
        "❌ Произошла ошибка. Пожалуйста, начните запись заново.",
        reply_markup=None
    )
    return ConversationHandler.END
    
    await query.edit_message_text(
        "❌ Произошла ошибка. Пожалуйста, начните запись заново.",
        reply_markup=get_main_menu_keyboard(is_admin=False)
    )
    return ConversationHandler.END

async def client_input_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода имени клиента"""
    client_name = update.message.text.strip()
    
    if len(client_name) < 2:
        await update.message.reply_text(
            "❌ Имя слишком короткое. Пожалуйста, введите ваше настоящее имя и фамилию:",
            reply_markup=get_cancel_keyboard()
        )
        return TYPING_NAME
    
    # Сохраняем имя в context
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
    
    # Сохраняем контакт в context
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
    print("🔍 DEBUG: Начало client_input_request")
    
    client_request = update.message.text.strip()
    
    if client_request.lower() == 'пропустить':
        client_request = "Не указано"
    
    # Получаем все данные из context
    selected_slot = context.user_data.get('selected_slot')
    client_name = context.user_data.get('client_name')
    client_contact = context.user_data.get('client_contact')
    client_chat_id = update.effective_user.id
    
    print(f"🔍 DEBUG: Данные для записи - имя: {client_name}, контакт: {client_contact}, слот: {selected_slot}")
    
    if not all([selected_slot, client_name, client_contact]):
        await update.message.reply_text(
            "❌ Произошла ошибка. Не все данные заполнены. Пожалуйста, начните запись заново.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        return ConversationHandler.END
    
    # Сохраняем запись в базу данных
    success = book_appointment(
        slot_id=selected_slot['id'],
        client_name=client_name,
        client_contact=client_contact,
        client_request=client_request
    )
    
    if success:
        # ✅ ОТПРАВЛЯЕМ УВЕДОМЛЕНИЯ
        try:
            print("🔍 DEBUG: Начинаем отправку уведомлений")
        
            # 1. Уведомление админам о новой записи
            await working_reminder_service.send_new_appointment_notification(
                client_name=client_name,
                appointment_datetime=selected_slot['datetime'],
                client_contact=client_contact,
                client_request=client_request
            )
        
            print("🔍 DEBUG: Уведомление админам отправлено")
        
            # 2. Сохраняем напоминание в БД для отправки за 24 часа
            working_reminder_service.save_reminder_to_db(
                client_chat_id=client_chat_id,
                client_name=client_name,
                appointment_datetime=selected_slot['datetime']
            )
        
            print("🔍 DEBUG: Напоминание сохранено в БД")
        
        except Exception as e:
            print(f"❌ DEBUG: Ошибка при отправке уведомлений: {e}")
            import traceback
            print(f"❌ DEBUG: Подробности: {traceback.format_exc()}")
        
        # Сообщение для клиента
        client_message = (
            "🎉 **Запись успешно оформлена!**\n\n"
            f"📅 **Время:** {format_datetime(selected_slot['datetime'])}\n"
            f"👤 **Имя:** {client_name}\n"
            f"📞 **Контакт:** {client_contact}\n"
            f"📝 **Запрос:** {client_request}\n\n"
            "🔔 **Вы получите напоминание за 24 часа до консультации.**\n\n"
            "Если у вас есть вопросы, свяжитесь с администратором."
        )
        
        await update.message.reply_text(
            client_message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
        
        print("🔍 DEBUG: Клиенту отправлено подтверждение")
    else:
        await update.message.reply_text(
            "❌ Произошла ошибка при записи. Пожалуйста, попробуйте позже или свяжитесь с администратором.",
            reply_markup=get_main_menu_keyboard(is_admin=False)
        )
    
    # Очищаем context
    context.user_data.clear()
    
    return ConversationHandler.END

async def client_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена процесса записи клиентом"""
    # Очищаем context
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Запись отменена.",
        reply_markup=get_main_menu_keyboard(is_admin=False)
    )
    
    return ConversationHandler.END