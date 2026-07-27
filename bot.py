import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === НАСТРОЙКИ ===
BOT_TOKEN = "8840715635:AAHdEpXvasiY9IeQKcjXXrM6Vxi7veCxLqw"  # Вставь сюда токен от BotFather
WEBAPP_URL = "https://saharok-nails.onrender.com"  # Твоя ссылка на Render

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


# === КЛАВИАТУРЫ ===
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅 Записаться на маникюр",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="📋 Каталог услуг и цены", callback_data="catalog"),
            InlineKeyboardButton(text="💸 Оформление возврата", callback_data="refund")
        ],
        [
            InlineKeyboardButton(text="💬 Связаться с администратором", url="https://t.me////...")
        ]
    ])
    return keyboard


# === ОБРАБОТЧИКИ КОМАНД И КНОПОК ===

@dp.message(CommandStart())
def start_cmd(message: types.Message):
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 🌸\n\n"
        "Добро пожаловать в студию эстетичного маникюра **Сахарок_nails** (СПб).\n\n"
        "Здесь ты можешь удобно записаться на процедуру, узнать цены или связаться с нами."
    )
    message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    catalog_text = (
        "✨ **Наш Прайс-лист:**\n\n"
        "💅 **Маникюр + Гель-лак** — 2 200 ₽ (1 ч 30 мин)\n"
        "• Снятие, гигиенический маникюр, выравнивание и покрытие цветом.\n\n"
        "💅 **Наращивание ногтей** — 3 500 ₽ (2 ч 15 мин)\n"
        "• Моделирование формы, наращивание и дизайн.\n\n"
        "📍 *Адрес студии:* Санкт-Петербург, ..."
    )
    await callback.message.edit_text(catalog_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@dp.callback_query(F.data == "refund")
async def show_refund_info(callback: types.CallbackQuery):
    refund_text = (
        "💸 **Правила отмены и возврата средств:**\n\n"
        "1. Отменить или перенести запись без потери предоплаты можно не позднее, чем за **12 часов** до визита.\n"
        "2. Для отмены записи напишите нашему администратору с указанием вашего имени и времени записи.\n"
        "3. Возврат предоплаты осуществляется на ту же карту в течение 1–3 рабочих дней.\n\n"
        "👇 Жми кнопку ниже для связи с админом:"
    )
    await callback.message.edit_text(refund_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


# === ПЛАНИРОВЩИК НАПОМИНАНИЙ ===

async def check_and_send_reminders():
    """Проверяет записи в БД и отправляет авто-напоминания за 24 часа и за 3 часа."""
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()

    # Добавляем колонки для отслеживания отправки напоминаний, если их нет
    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN reminded_24h INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE bookings ADD COLUMN reminded_3h INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Колонки уже созданы

    cursor.execute(
        "SELECT id, user_name, telegram_username, date, time, service_name, reminded_24h, reminded_3h FROM bookings")
    bookings = cursor.fetchall()

    now = datetime.now()

    for b in bookings:
        b_id, name, tg_user, b_date, b_time, service, r_24h, r_3h = b

        # Парсим дату и время записи
        try:
            booking_dt = datetime.strptime(f"{b_date} {b_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        time_diff = booking_dt - now

        # Ищем ID чата по tg_user (если юзернейм сохранен)
        if not tg_user:
            continue

        clean_tg = tg_user.replace("@", "").strip()

        # Напоминание за 24 часа (в интервале от 23 до 25 часов)
        if timedelta(hours=23) <= time_diff <= timedelta(hours=25) and not r_24h:
            msg = (
                f"🌸 **Напоминание о записи!**\n\n"
                f"Завтра в **{b_time}** ждем вас в Сахарок_nails на услугу **{service}**.\n\n"
                f"Если у вас изменились планы, пожалуйста, предупредите нас заранее!"
            )
            try:
                # Отправка сообщений по username через aiogram
                await bot.send_message(chat_id=f"@{clean_tg}", text=msg, parse_mode="Markdown")
                cursor.execute("UPDATE bookings SET reminded_24h = 1 WHERE id = ?", (b_id,))
                conn.commit()
            except Exception as e:
                print(f"Ошибка отправки 24h напоминания для {tg_user}: {e}")

        # Напоминание за 3 часа (в интервале от 2.5 до 3.5 часов)
        if timedelta(hours=2.5) <= time_diff <= timedelta(hours=3.5) and not r_3h:
            msg = (
                f"✨ **Уже скоро!**\n\n"
                f"Напоминаем, что ваш визит состоится сегодня в **{b_time}** ({service}).\n"
                f"До встречи в студии! 💖"
            )
            try:
                await bot.send_message(chat_id=f"@{clean_tg}", text=msg, parse_mode="Markdown")
                cursor.execute("UPDATE bookings SET reminded_3h = 1 WHERE id = ?", (b_id,))
                conn.commit()
            except Exception as e:
                print(f"Ошибка отправки 3h напоминания для {tg_user}: {e}")

    conn.close()


# === ЗАПУСК ===

async def main():
    # Запускаем планировщик проверки записей каждые 10 минут
    scheduler.add_job(check_and_send_reminders, 'interval', minutes=10)
    scheduler.start()

    print("🤖 Бот Сахарок_nails запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())