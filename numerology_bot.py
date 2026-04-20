import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from aiohttp import web
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация — ЭТИ ПЕРЕМЕННЫЕ НАДО ЗАПОЛНИТЬ В RENDER
TOKEN_BOT = os.environ.get("TOKEN_BOT")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# НАСТРОЙКИ ОПЛАТЫ — ЭТО ТОЖЕ НАДО ВПИСАТЬ В RENDER
YOOMONEY_SHOP_ID = os.environ.get("YOOMONEY_SHOP_ID", "")        # ID магазина в ЮKassa
YOOMONEY_SECRET_KEY = os.environ.get("YOOMONEY_SECRET_KEY", "")  # Секретный ключ
PRODUCT_PRICE = 590  # цена в рублях

# Хранилище пользователей (в памяти, при перезапуске очистится)
# Для продакшена лучше использовать базу данных
user_data = {}

# ======================
# Гайды (содержание продукта)
# ======================

FREE_GUIDES = {
    "1": "🔮 *Гайд для числа 1* 🔮\n\n"
         "Вы — лидер по жизни. Ваша стихия — солнце.\n"
         "✅ Сильные стороны: целеустремленность, независимость, смелость.\n"
         "⚠️ Слабые стороны: упрямство, эгоцентризм.\n"
         "🍀 Камни-талисманы: рубин, янтарь.\n"
         "💼 Карьера: руководитель, предприниматель.\n"
         "💖 Любовь: вам нужен партнер, который будет восхищаться вами.\n\n"
         "✨ *Совет дня*: Научитесь делегировать задачи.",

    "2": "🔮 *Гайд для числа 2* 🔮\n\n"
         "Вы — дипломат и миротворец.\n"
         "✅ Сильные стороны: чувствительность, тактичность, умение слушать.\n"
         "⚠️ Слабые стороны: нерешительность, зависимость от мнения других.\n"
         "🍀 Камни-талисманы: жемчуг, лунный камень.\n"
         "💼 Карьера: психолог, дипломат, учитель.\n"
         "💖 Любовь: вам нужна гармония и взаимопонимание.\n\n"
         "✨ *Совет дня*: Доверяйте своей интуиции.",

    "3": "🔮 *Гайд для числа 3* 🔮\n\n"
         "Вы — творец и оптимист.\n"
         "✅ Сильные стороны: креативность, общительность, чувство юмора.\n"
         "⚠️ Слабые стороны: разбросанность, поверхностность.\n"
         "🍀 Камни-талисманы: аметист, цитрин.\n"
         "💼 Карьера: артист, писатель, маркетолог.\n"
         "💖 Любовь: вам нужен вдохновляющий партнер.\n\n"
         "✨ *Совет дня*: Доведите начатое до конца.",

    "4": "🔮 *Гайд для числа 4* 🔮\n\n"
         "Вы — строитель и опора.\n"
         "✅ Сильные стороны: надежность, трудолюбие, практичность.\n"
         "⚠️ Слабые стороны: консерватизм, упертость.\n"
         "🍀 Камни-талисманы: сапфир, малахит.\n"
         "💼 Карьера: инженер, бухгалтер, строитель.\n"
         "💖 Любовь: вам нужна стабильность.\n\n"
         "✨ *Совет дня*: Позвольте себе немного спонтанности.",

    "5": "🔮 *Гайд для числа 5* 🔮\n\n"
         "Вы — путешественник и искатель приключений.\n"
         "✅ Сильные стороны: свобода, адаптивность, любопытство.\n"
         "⚠️ Слабые стороны: импульсивность, непостоянство.\n"
         "🍀 Камни-талисманы: бирюза, алмаз.\n"
         "💼 Карьера: журналист, фотограф, тревел-блогер.\n"
         "💖 Любовь: вам нужен партнер, который не будет ограничивать.\n\n"
         "✨ *Совет дня*: Попробуйте что-то новое сегодня.",

    "6": "🔮 *Гайд для числа 6* 🔮\n\n"
         "Вы — заботливый и ответственный.\n"
         "✅ Сильные стороны: любовь к семье, ответственность, гармония.\n"
         "⚠️ Слабые стороны: склонность к контролю, тревожность.\n"
         "🍀 Камни-талисманы: изумруд, нефрит.\n"
         "💼 Карьера: врач, учитель, дизайнер интерьеров.\n"
         "💖 Любовь: вы созданы для семьи.\n\n"
         "✨ *Совет дня*: Найдите время для себя.",

    "7": "🔮 *Гайд для числа 7* 🔮\n\n"
         "Вы — мыслитель и философ.\n"
         "✅ Сильные стороны: мудрость, интуиция, аналитический ум.\n"
         "⚠️ Слабые стороны: замкнутость, перфекционизм.\n"
         "🍀 Камни-талисманы: аметист, лунный камень.\n"
         "💼 Карьера: ученый, исследователь, программист.\n"
         "💖 Любовь: вам нужен умный и глубокий партнер.\n\n"
         "✨ *Совет дня*: Выйдите из зоны комфорта.",

    "8": "🔮 *Гайд для числа 8* 🔮\n\n"
         "Вы — маг и финансист.\n"
         "✅ Сильные стороны: целеустремленность, властность, успех.\n"
         "⚠️ Слабые стороны: жадность, авторитарность.\n"
         "🍀 Камни-талисманы: оникс, гранат.\n"
         "💼 Карьера: бизнесмен, банкир, юрист.\n"
         "💖 Любовь: вам нужен партнер, который разделяет амбиции.\n\n"
         "✨ *Совет дня*: Делитесь успехами с близкими.",

    "9": "🔮 *Гайд для числа 9* 🔮\n\n"
         "Вы — гуманист и альтруист.\n"
         "✅ Сильные стороны: сострадание, мудрость, щедрость.\n"
         "⚠️ Слабые стороны: расточительность, наивность.\n"
         "🍀 Камни-талисманы: рубин, гранат.\n"
         "💼 Карьера: благотворительность, искусство, духовный наставник.\n"
         "💖 Любовь: вам нужен идеалист.\n\n"
         "✨ *Совет дня*: Не забывайте о себе, помогая другим.",
}

# Инструкция по расчету числа судьбы
FATE_NUMBER_INSTRUCTION = (
    "📜 *Как рассчитать число судьбы?*\n\n"
    "Сложи все цифры своей даты рождения до получения однозначного числа.\n\n"
    "*Пример:* 15.04.1995\n"
    "1+5+0+4+1+9+9+5 = 34\n"
    "3+4 = 7\n\n"
    "👉 Ваше число судьбы — *7*\n\n"
    "👇 *Напиши мне свою дату рождения в формате ДД.ММ.ГГГГ*\n"
    "Например: 15.04.1995"
)

# Платный гайд (содержание того, что покупают)
PAID_GUIDE = {
    "1": "💰 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 1* 💰\n\n"
         "🔥 РАСШИРЕННАЯ ВЕРСИЯ 🔥\n\n"
         "• Детальная характеристика личности\n"
         "• Совместимость со всеми числами\n"
         "• Карьерный гороскоп на год\n"
         "• Любовный гороскоп\n"
         "• Финансовые прогнозы\n"
         "• Ритуалы на удачу\n"
         "• 10 советов от нумеролога\n\n"
         "✨ Спасибо за покупку! ✨",
    # Для остальных чисел аналогично, можно скопировать структуру
}

# Заполним для всех чисел (упрощенно, в реальности сделай уникальное содержание)
for i in range(1, 10):
    if str(i) not in PAID_GUIDE:
        PAID_GUIDE[str(i)] = f"💰 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА {i}* 💰\n\n" + PAID_GUIDE["1"].split("\n\n", 1)[1]

# ======================
# Команды бота
# ======================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и инструкция"""
    user = update.effective_user
    await update.message.reply_text(
        f"🌟 Привет, {user.first_name}! Я нумерологический бот.\n\n"
        f"{FATE_NUMBER_INSTRUCTION}\n\n"
        f"📌 После расчета я дам тебе бесплатный гайд по твоему числу и предложу купить полную версию за {PRODUCT_PRICE}₽."
    )

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает дату рождения и рассчитывает число судьбы"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Проверяем формат даты
    parts = text.split('.')
    if len(parts) != 3:
        await update.message.reply_text(
            "❌ Неверный формат.\n"
            "Напиши дату в формате: *ДД.ММ.ГГГГ*\n"
            "Например: 15.04.1995",
            parse_mode="Markdown"
        )
        return
    
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        
        # Простая проверка валидности
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1000 <= year <= 2026):
            raise ValueError
        
        # Рассчитываем число судьбы
        sum_digits = sum(int(d) for d in text if d.isdigit())
        while sum_digits > 9:
            sum_digits = sum(int(d) for d in str(sum_digits))
        
        fate_number = str(sum_digits)
        
        # Сохраняем данные пользователя
        user_data[user_id] = {
            "birth_date": text,
            "fate_number": fate_number,
            "paid": False
        }
        
        # Отправляем бесплатный гайд
        free_guide = FREE_GUIDES.get(fate_number, FREE_GUIDES["1"])
        
        # Кнопка для покупки платного гайда
        keyboard = [
            [InlineKeyboardButton(f"💎 Купить полный гайд за {PRODUCT_PRICE}₽", callback_data="buy_guide")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔢 *Твоё число судьбы: {fate_number}*\n\n"
            f"{free_guide}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔥 Хочешь получить *полную расшифровку*?\n"
            f"В платной версии: совместимость, гороскопы, ритуалы и многое другое!\n"
            f"💳 Цена: {PRODUCT_PRICE}₽",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        logger.info(f"Пользователь {user_id} получил число {fate_number}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверная дата.\n"
            "Попробуй еще раз в формате: *ДД.ММ.ГГГГ*",
            parse_mode="Markdown"
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия кнопок"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if query.data == "buy_guide":
        # Проверяем, не купил ли уже пользователь
        if user_data.get(user_id, {}).get("paid"):
            await query.edit_message_text(
                "✅ У тебя уже есть полный гайд!\n"
                "Вот он:",
                parse_mode="Markdown"
            )
            await send_paid_guide(query.message, user_id)
            return
        
        # Создаем платежную ссылку (через ЮKassa или любой другой сервис)
        payment_link = await create_payment_link(user_id, query.message)
        
        if payment_link:
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить 590₽", url=payment_link)],
                [InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_payment")]
            ]
            await query.edit_message_text(
                f"💸 *Оплата полного гайда*\n\n"
                f"Сумма: {PRODUCT_PRICE}₽\n\n"
                f"👉 *После оплаты нажми «Проверить оплату»*\n\n"
                f"📌 Ссылка действительна 1 час.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Если платежная система не настроена — тестовый режим
            keyboard = [
                [InlineKeyboardButton("🎁 Получить тестовый доступ", callback_data="test_paid")]
            ]
            await query.edit_message_text(
                f"⚠️ *Тестовый режим*\n\n"
                f"Платежная система пока не настроена.\n"
                f"Нажми кнопку ниже для тестового доступа к полному гайду.\n\n"
                f"💡 *Для реальных продаж:* добавь в переменные окружения YOOMONEY_SHOP_ID и YOOMONEY_SECRET_KEY",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == "check_payment":
        # Проверяем статус оплаты
        if await check_payment_status(user_id):
            user_data[user_id]["paid"] = True
            await query.edit_message_text("✅ *Оплата подтверждена!* ✅\n\nВот твой полный гайд:", parse_mode="Markdown")
            await send_paid_guide(query.message, user_id)
        else:
            await query.answer("❌ Оплата не найдена. Если ты только что оплатил, подожди 1-2 минуты.", show_alert=True)
    
    elif query.data == "test_paid":
        # Тестовый доступ (для отладки)
        user_data[user_id]["paid"] = True
        await query.edit_message_text("🎁 *Тестовый доступ активирован!* 🎁\n\nВот твой полный гайд:", parse_mode="Markdown")
        await send_paid_guide(query.message, user_id)

async def send_paid_guide(message, user_id):
    """Отправляет платный гайд пользователю"""
    fate_number = user_data.get(user_id, {}).get("fate_number", "1")
    guide = PAID_GUIDE.get(fate_number, PAID_GUIDE["1"])
    
    await message.reply_text(
        f"{guide}\n\n"
        f"📌 Сохрани этот гайд, он всегда будет у тебя в чате с ботом.\n"
        f"🌟 Спасибо за доверие! 🌟",
        parse_mode="Markdown"
    )

# ======================
# Функции оплаты (ЮKassa / YooMoney)
# ======================

async def create_payment_link(user_id: int, message) -> str:
    """
    Создает платежную ссылку через ЮKassa.
    Возвращает URL для оплаты или None при ошибке.
    """
    if not YOOMONEY_SHOP_ID or not YOOMONEY_SECRET_KEY:
        logger.warning("Платежная система не настроена")
        return None
    
    import uuid
    import aiohttp
    
    payment_id = str(uuid.uuid4())
    return_url = f"https://t.me/{message.get_bot().username}?start=payment_{payment_id}"
    
    # Сохраняем информацию о платеже
    if 'payments' not in user_data:
        user_data['payments'] = {}
    user_data['payments'][payment_id] = {
        "user_id": user_id,
        "amount": PRODUCT_PRICE,
        "status": "pending"
    }
    
    # Запрос к API ЮKassa
    url = "https://api.yookassa.ru/v3/payments"
    auth = aiohttp.BasicAuth(YOOMONEY_SHOP_ID, YOOMONEY_SECRET_KEY)
    
    payload = {
        "amount": {
            "value": str(PRODUCT_PRICE),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": f"Полный нумерологический гайд для пользователя {user_id}",
        "metadata": {
            "user_id": str(user_id),
            "payment_id": payment_id
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, auth=auth) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["confirmation"]["confirmation_url"]
                else:
                    logger.error(f"Ошибка платежа: {await resp.text()}")
                    return None
    except Exception as e:
        logger.error(f"Исключение при создании платежа: {e}")
        return None

async def check_payment_status(user_id: int) -> bool:
    """
    Проверяет статус последнего платежа пользователя.
    В реальности нужно проверять через webhook от ЮKassa.
    """
    # Упрощенная версия — в реальности используй webhook
    # Пока возвращаем False для реального режима, True — для тестового
    if not YOOMONEY_SHOP_ID:
        return False  # В тестовом режиме не проверяем
    return False

# Webhook для уведомлений от ЮKassa
async def yookassa_webhook(request):
    """Обработчик уведомлений от ЮKassa об оплате"""
    try:
        data = await request.json()
        logger.info(f"Получен webhook от ЮKassa: {data}")
        
        # Проверяем подпись (нужно добавить)
        if data.get("event") == "payment.succeeded":
            payment_id = data.get("object", {}).get("metadata", {}).get("payment_id")
            user_id = data.get("object", {}).get("metadata", {}).get("user_id")
            
            if user_id and payment_id:
                user_id = int(user_id)
                if user_id in user_data:
                    user_data[user_id]["paid"] = True
                    logger.info(f"Оплата подтверждена для пользователя {user_id}")
                    
                    # Отправляем уведомление пользователю (если бот может писать)
                    # Для этого нужен доступ к боту через глобальную переменную
                    try:
                        from numerology_bot import application
                        await application.bot.send_message(
                            chat_id=user_id,
                            text="✅ *Оплата прошла успешно!* ✅\n\nОтправляю твой полный гайд...",
                            parse_mode="Markdown"
                        )
                        # Отправляем гайд
                        fate_number = user_data[user_id].get("fate_number", "1")
                        guide = PAID_GUIDE.get(fate_number, PAID_GUIDE["1"])
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=guide,
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление: {e}")
        
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка в webhook ЮKassa: {e}")
        return web.Response(text="Error", status=500)

# ======================
# Запуск бота
# ======================

async def webhook_handler(request):
    """Обработчик вебхуков от Telegram"""
    try:
        data = await request.json()
        bot_app = request.app['bot_app']
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return web.Response(text="Error", status=500)

async def health_handler(request):
    return web.Response(text="OK", status=200)

def setup_application():
    """Настройка приложения"""
    app = Application.builder().token(TOKEN_BOT).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    return app

async def main():
    logger.info("🚀 Запуск нумерологического бота...")
    
    if not TOKEN_BOT:
        logger.error("❌ TOKEN_BOT не задан")
        return
    
    global application
    application = setup_application()
    await application.initialize()
    
    if WEBHOOK_URL:
        logger.info(f"🌐 Режим вебхука на порту {PORT}")
        webhook_full_url = f"{WEBHOOK_URL}/webhook"
        result = await application.bot.set_webhook(url=webhook_full_url, drop_pending_updates=True)
        
        if result:
            logger.info(f"✅ Вебхук установлен: {webhook_full_url}")
        else:
            logger.error("❌ Не удалось установить вебхук")
            return
        
        # Создаем aiohttp сервер
        app = web.Application()
        app['bot_app'] = application
        app.router.add_post('/webhook', webhook_handler)
        app.router.add_post('/yookassa_webhook', yookassa_webhook)  # Для уведомлений от ЮKassa
        app.router.add_get('/health', health_handler)
        app.router.add_get('/', health_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        logger.info(f"✅ Бот запущен на порту {PORT}")
        await asyncio.Event().wait()
    else:
        logger.warning("⚠️ WEBHOOK_URL не указан, используем polling")
        await application.start()
        await application.updater.start_polling()
        logger.info("✅ Бот запущен в режиме polling")
        
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
