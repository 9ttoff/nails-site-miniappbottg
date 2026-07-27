import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8840715635:AAHdEpXvasiY9IeQKcjXXrM6Vxi7veCxLqw"  # Токен от @BotFather
ADMIN_CHAT_ID = 2001448448          # Твой численный ID
WEBAPP_URL = "https://saharok-nails.onrender.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💅 Записаться на маникюр", 
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ],
        [
            InlineKeyboardButton(text="📋 Прайс-лист", callback_data="catalog"),
            InlineKeyboardButton(text="💸 Отмена и возврат", callback_data="refund")
        ]
    ])

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    welcome_text = (
        f"Привет, {message.from_user.first_name}! 🌸\n\n"
        "Добро пожаловать в студию эстетичного маникюра **Сахарок_nails**.\n\n"
        "Нажми кнопку ниже, чтобы выбрать удобную дату и время для записи!"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    catalog_text = (
        "✨ **Наш Прайс-лист:**\n\n"
        "💅 **Маникюр + Гель-лак** — 2 200 ₽ (1 ч 30 мин)\n"
        "💅 **Наращивание ногтей** — 3 500 ₽ (2 ч 15 мин)\n"
        "💅 **Снятие + Гигиенический маникюр** — 1 200 ₽ (45 мин)"
    )
    await callback.message.edit_text(catalog_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "refund")
async def show_refund_info(callback: types.CallbackQuery):
    refund_text = (
        "💸 **Правила отмены записи:**\n\n"
        "1. Перенести или отменить запись можно не позднее чем за **12 часов** до начала процедуры.\n"
        "2. Для отмены свяжитесь с администратором."
    )
    await callback.message.edit_text(refund_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def check_and_send_reminders():
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, user_name, telegram_username, date, time, service_name, reminded_24h, reminded_3h FROM bookings")
    bookings = cursor.fetchall()
    now = datetime.now()

    for b in bookings:
        b_id, name, tg_user, b_date, b_time, service, r_24h, r_3h = b
        
        try:
            booking_dt = datetime.strptime(f"{b_date} {b_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            continue

        time_diff = booking_dt - now

        if not tg_user:
            continue
        
        clean_tg = tg_user.replace("@", "").strip()

        if timedelta(hours=23) <= time_diff <= timedelta(hours=25) and not r_24h:
            msg = f"🌸 **Напоминание!** Завтра в **{b_time}** у вас запись в Сахарок_nails ({service})."
            try:
                await bot.send_message(chat_id=f"@{clean_tg}", text=msg, parse_mode="Markdown")
                cursor.execute("UPDATE bookings SET reminded_24h = 1 WHERE id = ?", (b_id,))
                conn.commit()
            except Exception as e:
                print(f"Ошибка отправки 24h: {e}")

        if timedelta(hours=2.5) <= time_diff <= timedelta(hours=3.5) and not r_3h:
            msg = f"✨ **Уже скоро!** Сегодня в **{b_time}** ждем вас в Сахарок_nails ({service})."
            try:
                await bot.send_message(chat_id=f"@{clean_tg}", text=msg, parse_mode="Markdown")
                cursor.execute("UPDATE bookings SET reminded_3h = 1 WHERE id = ?", (b_id,))
                conn.commit()
            except Exception as e:
                print(f"Ошибка отправки 3h: {e}")

    conn.close()

# Запуск планировщика при старте бота в активном event loop
@dp.startup()
async def on_startup():
    if not scheduler.running:
        scheduler.add_job(check_and_send_reminders, 'interval', minutes=10)
        scheduler.start()
