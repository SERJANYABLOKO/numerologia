import os
import logging
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация — ЗАПОЛНИТЬ В RENDER
TOKEN_BOT = os.environ.get("TOKEN_BOT")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

# Настройки оплаты (оставь пустыми для тестового режима)
YOOMONEY_SHOP_ID = os.environ.get("YOOMONEY_SHOP_ID", "")
YOOMONEY_SECRET_KEY = os.environ.get("YOOMONEY_SECRET_KEY", "")
PRODUCT_PRICE = 590

# Хранилище пользователей
user_data = {}

# ======================
# БЕСПЛАТНЫЕ ГАЙДЫ (числа 1-9)
# ======================

FREE_GUIDES = {
    "1": "🔮 *ЧИСЛО 1 - ЛИДЕР* 🔮\n\n"
         "Вы прирожденный лидер. Ваша энергия — это солнце, вокруг которого вращаются другие.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Целеустремленность\n"
         "• Независимость\n"
         "• Смелость и инициативность\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Упрямство\n"
         "• Эгоцентризм\n"
         "• Нетерпеливость\n\n"
         "🍀 *Камень-талисман:* Рубин, Янтарь\n"
         "💼 *Лучшие профессии:* Руководитель, предприниматель, изобретатель\n"
         "💖 *В любви:* Вам нужен партнер, который будет восхищаться вами\n\n"
         "✨ *Совет дня:* Научитесь делегировать задачи и доверять другим",

    "2": "🔮 *ЧИСЛО 2 - ДИПЛОМАТ* 🔮\n\n"
         "Вы — миротворец и дипломат. Ваша сила в мягкости и умении находить компромиссы.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Чувствительность\n"
         "• Тактичность\n"
         "• Умение слушать\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Нерешительность\n"
         "• Зависимость от мнения других\n"
         "• Склонность к тревоге\n\n"
         "🍀 *Камень-талисман:* Жемчуг, Лунный камень\n"
         "💼 *Лучшие профессии:* Психолог, дипломат, учитель\n"
         "💖 *В любви:* Вам нужна гармония и взаимопонимание\n\n"
         "✨ *Совет дня:* Доверяйте своей интуиции",

    "3": "🔮 *ЧИСЛО 3 - ТВОРЕЦ* 🔮\n\n"
         "Вы — творческая личность и оптимист. Ваша жизнь — это яркое шоу.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Креативность\n"
         "• Общительность\n"
         "• Чувство юмора\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Разбросанность\n"
         "• Поверхностность\n"
         "• Эмоциональные качели\n\n"
         "🍀 *Камень-талисман:* Аметист, Цитрин\n"
         "💼 *Лучшие профессии:* Артист, писатель, маркетолог\n"
         "💖 *В любви:* Вам нужен вдохновляющий партнер\n\n"
         "✨ *Совет дня:* Доводите начатое до конца",

    "4": "🔮 *ЧИСЛО 4 - СТРОИТЕЛЬ* 🔮\n\n"
         "Вы — опора и фундамент. На вас держится любой проект.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Надежность\n"
         "• Трудолюбие\n"
         "• Практичность\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Консерватизм\n"
         "• Упертость\n"
         "• Склонность к рутине\n\n"
         "🍀 *Камень-талисман:* Сапфир, Малахит\n"
         "💼 *Лучшие профессии:* Инженер, бухгалтер, строитель\n"
         "💖 *В любви:* Вам нужна стабильность\n\n"
         "✨ *Совет дня:* Позвольте себе немного спонтанности",

    "5": "🔮 *ЧИСЛО 5 - ПУТЕШЕСТВЕННИК* 🔮\n\n"
         "Вы — свобода и приключения. Жизнь в движении — ваш девиз.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Адаптивность\n"
         "• Любопытство\n"
         "• Энергичность\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Импульсивность\n"
         "• Непостоянство\n"
         "• Безответственность\n\n"
         "🍀 *Камень-талисман:* Бирюза, Алмаз\n"
         "💼 *Лучшие профессии:* Журналист, фотограф, тревел-блогер\n"
         "💖 *В любви:* Вам нужен партнер без ограничений\n\n"
         "✨ *Совет дня:* Попробуйте что-то новое сегодня",

    "6": "🔮 *ЧИСЛО 6 - ХРАНИТЕЛЬ* 🔮\n\n"
         "Вы — забота и ответственность. Семья — ваш главный приоритет.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Любовь к близким\n"
         "• Ответственность\n"
         "• Гармония\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Склонность к контролю\n"
         "• Тревожность\n"
         "• Жертвенность\n\n"
         "🍀 *Камень-талисман:* Изумруд, Нефрит\n"
         "💼 *Лучшие профессии:* Врач, учитель, дизайнер\n"
         "💖 *В любви:* Вы созданы для семьи\n\n"
         "✨ *Совет дня:* Найдите время для себя",

    "7": "🔮 *ЧИСЛО 7 - МЫСЛИТЕЛЬ* 🔮\n\n"
         "Вы — философ и аналитик. Ваш ум — главное оружие.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Мудрость\n"
         "• Интуиция\n"
         "• Аналитический ум\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Замкнутость\n"
         "• Перфекционизм\n"
         "• Скептицизм\n\n"
         "🍀 *Камень-талисман:* Аметист, Лабрадорит\n"
         "💼 *Лучшие профессии:* Ученый, программист, исследователь\n"
         "💖 *В любви:* Вам нужен умный партнер\n\n"
         "✨ *Совет дня:* Выйдите из зоны комфорта",

    "8": "🔮 *ЧИСЛО 8 - МАГ* 🔮\n\n"
         "Вы — финансист и властелин судьбы. Деньги любят вас.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Целеустремленность\n"
         "• Властность\n"
         "• Деловая хватка\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Жадность\n"
         "• Авторитарность\n"
         "• Склонность к манипуляциям\n\n"
         "🍀 *Камень-талисман:* Оникс, Гранат\n"
         "💼 *Лучшие профессии:* Бизнесмен, банкир, юрист\n"
         "💖 *В любви:* Вам нужен амбициозный партнер\n\n"
         "✨ *Совет дня:* Делитесь успехами с близкими",

    "9": "🔮 *ЧИСЛО 9 - ГУМАНИСТ* 🔮\n\n"
         "Вы — альтруист и мудрец. Вы пришли в этот мир помогать.\n\n"
         "✅ *Сильные стороны:*\n"
         "• Сострадание\n"
         "• Мудрость\n"
         "• Щедрость\n\n"
         "⚠️ *Слабые стороны:*\n"
         "• Расточительность\n"
         "• Наивность\n"
         "• Склонность к иллюзиям\n\n"
         "🍀 *Камень-талисман:* Рубин, Гранат\n"
         "💼 *Лучшие профессии:* Благотворительность, искусство, наставник\n"
         "💖 *В любви:* Вам нужен идеалист\n\n"
         "✨ *Совет дня:* Не забывайте о себе, помогая другим"
}

# ======================
# ПЛАТНЫЕ ГАЙДЫ (расширенные версии)
# ======================

PAID_GUIDES = {
    "1": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 1* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Карьерный гороскоп на 2025-2026 год\n"
         "• Любовный гороскоп по месяцам\n"
         "• Финансовый прогноз и денежные ритуалы\n"
         "• 7 сильных ритуалов на удачу\n"
         "• Медитации для активации энергии\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨\n"
         "Сохраните это сообщение — оно всегда будет у вас в чате",
    
    "2": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 2* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Карьерный гороскоп на 2025-2026 год\n"
         "• Любовный гороскоп по месяцам\n"
         "• Как развить интуицию — практические упражнения\n"
         "• Медитации для баланса энергии\n"
         "• Советы по улучшению отношений\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "3": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 3* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Как раскрыть творческий потенциал\n"
         "• Карьерный гороскоп для творческих профессий\n"
         "• Любовный гороскоп и советы по отношениям\n"
         "• Ритуалы на вдохновение\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "4": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 4* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Карьерный гороскоп и финансы\n"
         "• Как найти баланс между работой и отдыхом\n"
         "• Упражнения для снятия стресса\n"
         "• Ритуалы на стабильность и процветание\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "5": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 5* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Гайд по лучшим направлениям для путешествий\n"
         "• Как превратить хаос в порядок\n"
         "• Финансовые возможности и риски\n"
         "• Медитации для энергии и свободы\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "6": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 6* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Семейный гороскоп и отношения\n"
         "• Как не растворяться в других\n"
         "• Ритуалы для гармонии в доме\n"
         "• Советы по воспитанию детей\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "7": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 7* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Как развить сверхспособности\n"
         "• Медитации для глубокого самопознания\n"
         "• Духовные практики по дате рождения\n"
         "• Кармические задачи\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "8": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 8* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Финансовый гороскоп и денежные каналы\n"
         "• Как привлечь богатство — 5 ритуалов\n"
         "• Карьерный гороскоп для бизнеса\n"
         "• Магические практики для успеха\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨",
    
    "9": "💎 *ПОЛНЫЙ ГАЙД ДЛЯ ЧИСЛА 9* 💎\n\n"
         "🔥 *РАСШИРЕННАЯ ВЕРСИЯ* 🔥\n\n"
         "📖 *Содержание:*\n"
         "• Полная характеристика личности (10 страниц)\n"
         "• Совместимость со всеми числами судьбы\n"
         "• Ваше предназначение в этом мире\n"
         "• Как помогать и не выгорать\n"
         "• Медитации для принятия себя\n"
         "• Ритуалы на завершение циклов\n"
         "• 20 советов от профессионального нумеролога\n\n"
         "✨ *Спасибо за покупку!* ✨"
}

# Заполняем для всех чисел, если чего-то не хватает
for i in range(1, 10):
    if str(i) not in PAID_GUIDES:
        PAID_GUIDES[str(i)] = PAID_GUIDES["1"].replace("ЧИСЛА 1", f"ЧИСЛА {i}")

# ======================
# КОМАНДЫ БОТА
# ======================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие и инструкция по расчету числа судьбы"""
    user = update.effective_user
    
    welcome_text = (
        f"🌟 *Привет, {user.first_name}!* 🌟\n\n"
        "Я нумерологический бот. Я помогу тебе узнать твое *число судьбы* и получить персонализированный гайд.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "*📜 КАК РАССЧИТАТЬ ЧИСЛО СУДЬБЫ?*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Сложи все цифры своей даты рождения до получения однозначного числа.\n\n"
        "*Пример:* 15.04.1995\n"
        "1+5+0+4+1+9+9+5 = 34 → 3+4 = *7*\n\n"
        "👉 Твое число судьбы — *7*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "*👇 Отправь мне свою дату рождения*\n"
        "в формате: *ДД.ММ.ГГГГ*\n\n"
        "Например: *15.04.1995*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎁 *Бесплатно:* ты получишь базовый гайд по своему числу\n"
        f"💎 *За {PRODUCT_PRICE}₽:* полную расшифровку с гороскопами, ритуалами и советами"
    )
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает дату рождения и рассчитывает число судьбы"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Очищаем текст от лишних символов
    import re
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
    
    if not date_match:
        await update.message.reply_text(
            "❌ *Неверный формат*\n\n"
            "Пожалуйста, отправь дату в формате:\n"
            "*ДД.ММ.ГГГГ*\n\n"
            "Пример: *15.04.1995*\n"
            "Пример: *7.12.1990*",
            parse_mode="Markdown"
        )
        return
    
    try:
        day, month, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        
        # Проверка валидности даты
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2026):
            await update.message.reply_text(
                "❌ *Неверная дата*\n\n"
                "Проверь, что:\n"
                "• День от 1 до 31\n"
                "• Месяц от 1 до 12\n"
                "• Год от 1900 до 2026",
                parse_mode="Markdown"
            )
            return
        
        # Рассчитываем число судьбы
        sum_digits = 0
        for char in f"{day}{month}{year}":
            if char.isdigit():
                sum_digits += int(char)
        
        while sum_digits > 9:
            sum_digits = sum(int(d) for d in str(sum_digits))
        
        fate_number = str(sum_digits)
        
        # Сохраняем данные пользователя
        user_data[user_id] = {
            "birth_date": f"{day:02d}.{month:02d}.{year}",
            "fate_number": fate_number,
            "paid": False
        }
        
        # Получаем бесплатный гайд
        free_guide = FREE_GUIDES.get(fate_number, FREE_GUIDES["1"])
        
        # Кнопка для покупки
        keyboard = [
            [InlineKeyboardButton(f"💎 Купить полный гайд за {PRODUCT_PRICE}₽", callback_data="buy_guide")],
            [InlineKeyboardButton("🔄 Рассчитать заново", callback_data="recalculate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"🔮 *ТВОЕ ЧИСЛО СУДЬБЫ: {fate_number}* 🔮\n\n"
            f"{free_guide}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌟 *ХОЧЕШЬ БОЛЬШЕ?* 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"В *полной версии* тебя ждет:\n"
            f"📖 10 страниц персонализированной информации\n"
            f"💑 Совместимость со всеми числами\n"
            f"📅 Гороскоп на 2025-2026 год\n"
            f"💰 Финансовые прогнозы и ритуалы\n"
            f"✨ 7 сильных практик для активации энергии\n"
            f"🎯 20 советов от нумеролога\n\n"
            f"💳 *Цена: {PRODUCT_PRICE}₽* — всего один раз и гайд навсегда с тобой",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        
        logger.info(f"Пользователь {user_id} ({update.effective_user.first_name}) получил число {fate_number}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке даты: {e}")
        await update.message.reply_text(
            "❌ *Ошибка*\n\n"
            "Что-то пошло не так. Попробуй еще раз отправить дату в формате *ДД.ММ.ГГГГ*",
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
                "✅ *У тебя уже есть полный гайд!*\n\n"
                "Отправляю его еще раз 👇",
                parse_mode="Markdown"
            )
            await send_paid_guide(query.message, user_id)
            return
        
        # Создаем платежную ссылку
        payment_link = await create_payment_link(user_id)
        
        if payment_link:
            keyboard = [
                [InlineKeyboardButton("💳 Оплатить 590₽", url=payment_link)],
                [InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_payment")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_guide")]
            ]
            await query.edit_message_text(
                f"💸 *ОПЛАТА ПОЛНОГО ГАЙДА* 💸\n\n"
                f"💰 Сумма: *{PRODUCT_PRICE}₽*\n"
                f"🔢 Твое число: *{user_data[user_id]['fate_number']}*\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 *Инструкция:*\n"
                f"1. Нажми на кнопку оплаты\n"
                f"2. Оплати удобным способом\n"
                f"3. Вернись в бот и нажми «Проверить оплату»\n\n"
                f"⏰ Ссылка действительна 1 час\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"*После оплаты ты сразу получишь полный гайд!*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Тестовый режим (без реальной оплаты)
            keyboard = [
                [InlineKeyboardButton("🎁 Получить тестовый доступ", callback_data="test_paid")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_guide")]
            ]
            await query.edit_message_text(
                f"⚠️ *ТЕСТОВЫЙ РЕЖИМ* ⚠️\n\n"
                f"Платежная система пока не настроена.\n\n"
                f"Нажми кнопку ниже для *бесплатного тестового доступа* к полному гайду.\n\n"
                f"💡 *Для реальных продаж:*\n"
                f"Добавь в переменные окружения Render:\n"
                f"• YOOMONEY_SHOP_ID\n"
                f"• YOOMONEY_SECRET_KEY\n\n"
                f"Зарегистрироваться можно на yookassa.ru",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    elif query.data == "check_payment":
        # Проверяем статус оплаты
        if await check_payment_status(user_id):
            user_data[user_id]["paid"] = True
            await query.edit_message_text("✅ *Оплата подтверждена!* ✅\n\nОтправляю твой полный гайд 👇", parse_mode="Markdown")
            await send_paid_guide(query.message, user_id)
        else:
            await query.answer(
                "❌ Оплата не найдена.\n\nЕсли вы только что оплатили, подождите 1-2 минуты и нажмите снова.\n\nЕсли оплата не проходит, напишите @support", 
                show_alert=True
            )
    
    elif query.data == "test_paid":
        # Тестовый доступ
        user_data[user_id]["paid"] = True
        await query.edit_message_text("🎁 *Тестовый доступ активирован!* 🎁\n\nВот твой полный гайд 👇", parse_mode="Markdown")
        await send_paid_guide(query.message, user_id)
    
    elif query.data == "back_to_guide":
        # Возвращаемся к бесплатному гайду
        fate_number = user_data.get(user_id, {}).get("fate_number", "1")
        free_guide = FREE_GUIDES.get(fate_number, FREE_GUIDES["1"])
        
        keyboard = [
            [InlineKeyboardButton(f"💎 Купить полный гайд за {PRODUCT_PRICE}₽", callback_data="buy_guide")],
            [InlineKeyboardButton("🔄 Рассчитать заново", callback_data="recalculate")]
        ]
        
        await query.edit_message_text(
            f"🔮 *ТВОЕ ЧИСЛО СУДЬБЫ: {fate_number}* 🔮\n\n"
            f"{free_guide}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌟 *ХОЧЕШЬ ПОЛНУЮ ВЕРСИЮ?* 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💳 Цена: *{PRODUCT_PRICE}₽*\n\n"
            f"В полной версии: гороскопы, ритуалы, совместимость и 20 советов от нумеролога!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "recalculate":
        # Предлагаем ввести дату заново
        await query.edit_message_text(
            "🔄 *Введи свою дату рождения заново*\n\n"
            "Формат: *ДД.ММ.ГГГГ*\n\n"
            "Пример: *15.04.1995*",
            parse_mode="Markdown"
        )

async def send_paid_guide(message, user_id):
    """Отправляет платный гайд пользователю"""
    fate_number = user_data.get(user_id, {}).get("fate_number", "1")
    guide = PAID_GUIDES.get(fate_number, PAID_GUIDES["1"])
    
    await message.reply_text(
        f"{guide}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Сохрани это сообщение!*\n"
        f"Гайд всегда будет в твоем чате с ботом.\n\n"
        f"🌟 *Спасибо за доверие!* 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

# ======================
# ФУНКЦИИ ОПЛАТЫ
# ======================

async def create_payment_link(user_id: int) -> str:
    """
    Создает платежную ссылку через ЮKassa
    """
    if not YOOMONEY_SHOP_ID or not YOOMONEY_SECRET_KEY:
        logger.info("Платежная система не настроена, используем тестовый режим")
        return None
    
    import uuid
    import aiohttp
    
    payment_id = str(uuid.uuid4())
    
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
            "return_url": f"https://t.me/{TOKEN_BOT.split(':')[0] if TOKEN_BOT else 'bot'}"
        },
        "capture": True,
        "description": f"Нумерологический гайд для пользователя {user_id}",
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
                    logger.error(f"Ошибка ЮKassa: {await resp.text()}")
                    return None
    except Exception as e:
        logger.error(f"Исключение при создании платежа: {e}")
        return None

async def check_payment_status(user_id: int) -> bool:
    """
    Проверяет статус оплаты
    """
    # Если платежная система не настроена — тестовый режим
    if not YOOMONEY_SHOP_ID:
        return False
    
    # Здесь нужно реализовать проверку через API ЮKassa
    # Для простоты пока возвращаем False
    return False

# ======================
# WEBHOOK ДЛЯ ЮKASSA (опционально)
# ======================

async def yookassa_webhook(request):
    """Обработчик уведомлений от ЮKassa об успешной оплате"""
    try:
        data = await request.json()
        logger.info(f"Получен webhook от ЮKassa: {data}")
        
        if data.get("event") == "payment.succeeded":
            metadata = data.get("object", {}).get("metadata", {})
            user_id = metadata.get("user_id")
            payment_id = metadata.get("payment_id")
            
            if user_id:
                user_id = int(user_id)
                if user_id in user_data:
                    user_data[user_id]["paid"] = True
                    logger.info(f"✅ Оплата подтверждена для пользователя {user_id}")
                    
                    # Отправляем уведомление пользователю
                    try:
                        from numerology_bot import application
                        fate_number = user_data[user_id].get("fate_number", "1")
                        guide = PAID_GUIDES.get(fate_number, PAID_GUIDES["1"])
                        
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=f"✅ *Оплата прошла успешно!* ✅\n\nВот твой полный гайд:\n\n{guide}",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление: {e}")
        
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Ошибка в webhook ЮKassa: {e}")
        return web.Response(text="Error", status=500)

# ======================
# ЗАПУСК БОТА
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
    """Health check для Render"""
    return web.Response(text="OK", status=200)

def setup_application():
    """Настройка приложения Telegram бота"""
    app = Application.builder().token(TOKEN_BOT).build()
    
    # Команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    return app

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск нумерологического бота...")
    
    if not TOKEN_BOT:
        logger.error("❌ TOKEN_BOT не задан в переменных окружения")
        return
    
    global application
    application = setup_application()
    await application.initialize()
    
    if WEBHOOK_URL:
        logger.info(f"🌐 Режим вебхука на порту {PORT}")
        webhook_full_url = f"{WEBHOOK_URL}/webhook"
        
        result = await application.bot.set_webhook(
            url=webhook_full_url, 
            drop_pending_updates=True
        )
        
        if result:
            logger.info(f"✅ Вебхук успешно установлен: {webhook_full_url}")
        else:
            logger.error("❌ Не удалось установить вебхук")
            return
        
        # Создаем aiohttp сервер
        app = web.Application()
        app['bot_app'] = application
        app.router.add_post('/webhook', webhook_handler)
        app.router.add_post('/yookassa_webhook', yookassa_webhook)
        app.router.add_get('/health', health_handler)
        app.router.add_get('/', health_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()
        
        logger.info(f"✅ Бот успешно запущен на порту {PORT}")
        
        # Держим сервер запущенным
        await asyncio.Event().wait()
        
    else:
        logger.warning("⚠️ WEBHOOK_URL не указан, используем polling режим")
        await application.start()
        await application.updater.start_polling()
        logger.info("✅ Бот запущен в режиме polling")
        
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
