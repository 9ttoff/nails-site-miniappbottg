from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import sqlite3
import secrets

app = FastAPI()
security = HTTPBasic()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"


def init_db():
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            UNIQUE(date, time)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            phone TEXT,
            telegram_username TEXT,
            date TEXT,
            time TEXT,
            service_name TEXT,
            price INTEGER
        )
    ''')
    conn.commit()
    conn.close()


init_db()


class SlotModel(BaseModel):
    date: str
    time: str


class BookingModel(BaseModel):
    user_name: str
    phone: str
    telegram_username: str
    date: str
    time: str
    service_name: str
    price: int


class CancelBookingModel(BaseModel):
    booking_id: int


def auth_admin(credentials: HTTPBasicCredentials = Depends(security)):
    is_user_ok = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (is_user_ok and is_pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/", response_class=HTMLResponse)
def get_client_page():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/admin", response_class=HTMLResponse)
def get_admin_page(username: str = Depends(auth_admin)):
    with open("admin.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/slots")
def get_slots(date: str):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT time FROM slots WHERE date = ? ORDER BY time", (date,))
    rows = cursor.fetchall()
    conn.close()
    return {"slots": [r[0] for r in rows]}


@app.get("/api/admin/all-slots")
def get_all_slots(username: str = Depends(auth_admin)):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, time FROM slots ORDER BY date, time")
    rows = cursor.fetchall()
    conn.close()

    grouped = {}
    for date, time in rows:
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(time)
    return {"slots_by_date": grouped}


@app.get("/api/admin/bookings")
def get_bookings(username: str = Depends(auth_admin)):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, user_name, phone, telegram_username, date, time, service_name, price FROM bookings ORDER BY date, time")
    rows = cursor.fetchall()
    conn.close()

    bookings = []
    for r in rows:
        bookings.append({
            "id": r[0],
            "user_name": r[1],
            "phone": r[2],
            "telegram_username": r[3],
            "date": r[4],
            "time": r[5],
            "service_name": r[6],
            "price": r[7]
        })
    return {"bookings": bookings}


@app.post("/api/admin/add-slot")
def add_slot(slot: SlotModel, username: str = Depends(auth_admin)):
    try:
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO slots (date, time) VALUES (?, ?)", (slot.date, slot.time))
        conn.commit()
        conn.close()
        return {"status": "ok"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Такое окно уже существует")


@app.post("/api/admin/delete-slot")
def delete_slot(slot: SlotModel, username: str = Depends(auth_admin)):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM slots WHERE date = ? AND time = ?", (slot.date, slot.time))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.post("/api/admin/cancel-booking")
def cancel_booking(data: CancelBookingModel, username: str = Depends(auth_admin)):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()

    # Получаем информацию о записи
    cursor.execute("SELECT date, time FROM bookings WHERE id = ?", (data.booking_id,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        raise HTTPException(status_code=404, detail="Запись не найдена")

    date, time = booking[0], booking[1]

    # 1. Удаляем запись
    cursor.execute("DELETE FROM bookings WHERE id = ?", (data.booking_id,))

    # 2. Возвращаем слот обратно в свободные
    cursor.execute("INSERT OR IGNORE INTO slots (date, time) VALUES (?, ?)", (date, time))

    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.post("/api/book")
def create_booking(booking: BookingModel):
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM slots WHERE date = ? AND time = ?", (booking.date, booking.time))
    slot = cursor.fetchone()

    if not slot:
        conn.close()
        raise HTTPException(status_code=400, detail="К сожалению, это время уже занято.")

    cursor.execute("DELETE FROM slots WHERE date = ? AND time = ?", (booking.date, booking.time))
    cursor.execute(
        "INSERT INTO bookings (user_name, phone, telegram_username, date, time, service_name, price) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (booking.user_name, booking.phone, booking.telegram_username, booking.date, booking.time, booking.service_name,
         booking.price)
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Запись успешно оформлена!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)