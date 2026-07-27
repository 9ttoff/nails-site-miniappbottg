import sqlite3
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from bot import bot, dp, ADMIN_CHAT_ID

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    
    # Таблица свободных слотов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """)
    
    # Таблица записей клиентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            user_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            telegram_username TEXT,
            reminded_24h INTEGER DEFAULT 0,
            reminded_3h INTEGER DEFAULT 0
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# Фоновый запуск Telegram-бота вместе с сервером FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    polling_task.cancel()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

# Pydantic модели
class SlotRequest(BaseModel):
    date: str
    time: str

class BookingRequest(BaseModel):
    service_name: str
    price: int
    date: str
    time: str
    user_name: str
    phone: str
    telegram_username: Optional[str] = ""

# --- СТРАНИЦЫ ---

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def read_admin():
    with open("admin.html", "r", encoding="utf-8") as f:
        return f.read()

# --- API ЭНДПОИНТЫ ---

# 1. Получить список дат, где есть свободные окна (для календаря)
@app.get("/api/available-dates")
def get_available_dates():
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT date FROM slots ORDER BY date")
    rows = cursor.fetchall()
    conn.close()
    return {"dates": [r[0] for r in rows]}

# 2. Получить свободные слоты времени на конкретную дату
@app.get("/api/slots")
def get_slots(date: str):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM slots WHERE date = ? ORDER BY time", (date,))
    rows = cursor.fetchall()
    conn.close()
    return {"slots": [r[0] for r in rows]}

# 3. Добавить новое окно (из админки)
@app.post("/api/admin/add-slot")
def add_slot(slot: SlotRequest):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO slots (date, time) VALUES (?, ?)", (slot.date, slot.time))
    conn.commit()
    conn.close()
    return {"status": "ok"}

# 4. Создать новую запись клиента
@app.post("/api/book")
async def book_slot(data: BookingRequest):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    
    # Проверяем наличие слота
    cursor.execute("SELECT id FROM slots WHERE date = ? AND time = ?", (data.date, data.time))
    slot = cursor.fetchone()
    
    if not slot:
        conn.close()
        raise HTTPException(status_code=400, detail="Слот уже занят или недоступен")
    
    # Удаляем из свободных окон
    cursor.execute("DELETE FROM slots WHERE date = ? AND time = ?", (data.date, data.time))
    
    # Сохраняем бронирование
    cursor.execute("""
        INSERT INTO bookings (service_name, price, date, time, user_name, phone, telegram_username)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.service_name, data.price, data.date, data.time, data.user_name, data.phone, data.telegram_username))
    
    conn.commit()
    conn.close()

    # Мгновенное уведомление администратору в Telegram
    admin_text = (
        f"💅 **Новая запись!**\n\n"
        f"✨ **Услуга:** {data.service_name} ({data.price} ₽)\n"
        f"📅 **Дата и время:** {data.date} в {data.time}\n"
        f"👤 **Клиент:** {data.user_name}\n"
        f"📞 **Телефон:** {data.phone}\n"
        f"💬 **Telegram:** {data.telegram_username}"
    )
    
    try:
        if ADMIN_CHAT_ID != 2001448448:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")

    return {"status": "ok"}

# 5. Список всех записей клиентов (для админки)
@app.get("/api/admin/bookings")
def get_bookings():
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, service_name, price, date, time, user_name, phone, telegram_username FROM bookings ORDER BY date, time")
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r[0], "service_name": r[1], "price": r[2],
            "date": r[3], "time": r[4], "user_name": r[5],
            "phone": r[6], "telegram_username": r[7]
        })
    return {"bookings": result}
