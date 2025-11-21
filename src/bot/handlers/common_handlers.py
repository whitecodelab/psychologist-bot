from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, Application, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from src.config.settings import settings
from src.bot.keyboards.layouts import get_main_menu_keyboard
from src.database.core import init_database
from src.services.working_reminder_service import init_working_reminder_service, working_reminder_service
from telegram.ext import JobQueue

from src.bot.handlers.admin_handlers import (
    admin_add_slot_start, 
    admin_add_slot_input, 
    admin_cancel, 
    ADDING_SLOT,
    admin_show_appointments,
    admin_delete_slot_start,
    admin_delete_slot_confirm,
    DELETING_SLOT,
    admin_show_my_slots,
    admin_show_archive
)

from src.bot.handlers.client_handlers import (
    client_start_booking,
    client_choose_slot, 
    client_input_name,
    client_input_contact,
    client_input_request,
    client_cancel_booking,
    CHOOSING_SLOT, TYPING_NAME, TYPING_CONTACT, TYPING_REQUEST
)


# ===== ОСНОВНЫЕ КОМАНДЫ =====
import os
from telegram import InputFile

import os
from telegram import InputFile

import os
from telegram import InputFile

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с разными приветствиями для админов и клиентов"""
    user_id = update.effective_user.id
    is_admin = settings.is_admin(user_id)
    
    print(f"🔍 DEBUG start_command: user_id={user_id}, is_admin={is_admin}, username={update.effective_user.username}")
    
    # Получаем абсолютный путь к папке проекта
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assets_dir = os.path.join(base_dir, 'assets')
    
    # Проверяем разные варианты файлов
    photo_paths = [
        os.path.join(assets_dir, 'psychologist_photo.png'),
        os.path.join(assets_dir, 'psychologist_photo.jpg'),
        os.path.join(assets_dir, 'psychologist_photo.jpeg'),
    ]
    
    photo_path = None
    for path in photo_paths:
        if os.path.exists(path):
            photo_path = path
            print(f"✅ DEBUG: Найдено фото: {path}")
            break
    
    # РАЗНЫЕ ПРИВЕТСТВИЯ ДЛЯ АДМИНОВ И КЛИЕНТОВ
    
    if is_admin:
        # ПРИВЕТСТВИЕ ДЛЯ АДМИНИСТРАТОРА (без фото)
        admin_welcome_text = """
👋 Добро пожаловать в панель администратора!

Здесь вы можете управлять расписанием и просматривать записи клиентов.

Доступные функции:
• ➕ Добавить слот - создать новые слоты для записи
• 🗑️ Удалить слот - удалить свободные слоты
• 📋 Ближайшие записи - просмотреть все записи клиентов
• 👀 Мои слоты - посмотреть все слоты со статусами
        """.strip()
        
        await update.message.reply_text(
            admin_welcome_text,
            reply_markup=get_main_menu_keyboard(is_admin=True)
        )
        
    else:
        # ПРИВЕТСТВИЕ ДЛЯ КЛИЕНТА (с фото психолога)
        welcome_text = """
Добрый день! 👋

Меня зовут Александр. Я психолог с 10-летним опытом работы.

Я специализируюсь на:
• Работе с тревогой и стрессом
• Поиске жизненного баланса
• Преодолении кризисных ситуаций
• Развитии эмоционального интеллекта

Я постараюсь помочь вам найти внутреннюю гармонию и ресурсы для решения ваших задач.

Для записи на консультацию нажмите кнопку ниже 👇
        """.strip()
        
        try:
            # Для клиентов отправляем фото психолога
            if photo_path and os.path.exists(photo_path):
                print(f"🔍 DEBUG: Отправляем фото клиенту: {photo_path}")
                with open(photo_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=InputFile(photo),
                        caption=welcome_text,
                        reply_markup=get_main_menu_keyboard(is_admin=False)
                    )
            else:
                # Если фото не найдено, отправляем только текст
                print("❌ DEBUG: Фото не найдено, отправляем текст клиенту")
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=get_main_menu_keyboard(is_admin=False)
                )
                
        except Exception as e:
            print(f"❌ DEBUG: Ошибка при отправке фото клиенту: {e}")
            # Запасной вариант для клиента
            await update.message.reply_text(
                welcome_text,
                reply_markup=get_main_menu_keyboard(is_admin=False)
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text("📋 Используйте кнопки меню для навигации.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"❌ Ошибка: {context.error}")

# ===== НАСТРОЙКА ОБРАБОТЧИКОВ =====
def setup_handlers():
    """Настройка всех обработчиков бота"""
    application = Application.builder().token(settings.BOT_TOKEN).build()
    
    # ✅ ИНИЦИАЛИЗИРУЕМ РАБОЧИЙ СЕРВИС УВЕДОМЛЕНИЙ
    init_working_reminder_service(application.bot)
    
    # ✅ ДОБАВЛЯЕМ ПЕРИОДИЧЕСКУЮ ПРОВЕРКУ НАПОМИНАНИЙ
    async def check_reminders_callback(context):
        await working_reminder_service.check_and_send_reminders()
    
    # Проверяем напоминания каждые 5 минут
    job_queue = application.job_queue
    job_queue.run_repeating(check_reminders_callback, interval=300, first=10)  # 300 сек = 5 минут
    
    print("✅ Периодическая проверка напоминаний настроена")

    # Основные команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Админ: добавление слотов
    add_slot_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ Добавить слот$'), admin_add_slot_start)],
        states={ADDING_SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_slot_input)]},
        fallbacks=[MessageHandler(filters.Regex('^❌ Отмена$'), admin_cancel)]
    )
    application.add_handler(add_slot_conv_handler)

        # ConversationHandler для удаления слотов (админ)
    delete_slot_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^🗑️ Удалить слот$'), admin_delete_slot_start)
        ],
        states={
            DELETING_SLOT: [
                CallbackQueryHandler(admin_delete_slot_confirm, pattern='^(delete_slot_|cancel_deletion)')
            ]
        },
        fallbacks=[]  # Убираем fallbacks, так как отмена теперь через инлайн-кнопку
    )
    application.add_handler(delete_slot_conv_handler)

    # Админ: просмотр записей
    application.add_handler(MessageHandler(filters.Regex('^📋 Ближайшие записи$'), admin_show_appointments))
    
    # Админ: просмотр слотов (НОВАЯ КНОПКА)
    application.add_handler(MessageHandler(filters.Regex('^👀 Мои слоты$'), admin_show_my_slots))

    # Обработчик для кнопки "📚 Архив записей"
    application.add_handler(MessageHandler(filters.Regex('^📚 Архив записей$'), admin_show_archive))
    
    # Клиент: запись на консультацию
    client_booking_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📅 Записаться на консультацию$'), client_start_booking)],
        states={
            CHOOSING_SLOT: [CallbackQueryHandler(client_choose_slot, pattern='^(book_slot_|cancel_booking)')],
            TYPING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_input_name)],
            TYPING_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_input_contact)],
            TYPING_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, client_input_request)]
        },
        fallbacks=[MessageHandler(filters.Regex('^❌ Отмена$'), client_cancel_booking)]
    )
    application.add_handler(client_booking_conv_handler)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Инициализация БД
    init_database()
    
    print("✅ Обработчики настроены, запуск бота...")
    application.run_polling()