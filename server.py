<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Сахарок_nails — Запись</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg-color: #FFF5F7;
            --card-bg: #FFFFFF;
            --accent-pink: #FF85A1;
            --accent-pink-hover: #F26B8A;
            --text-dark: #4A4A4A;
            --text-muted: #888888;
            --green-available: #E8F5E9;
            --green-text: #2E7D32;
            --disabled-gray: #F0F0F0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-dark);
            margin: 0;
            padding: 16px;
        }

        .container {
            max-width: 480px;
            margin: 0 auto;
        }

        h2 {
            text-align: center;
            color: var(--accent-pink-hover);
            margin-bottom: 20px;
        }

        .card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 4px 15px rgba(255, 133, 161, 0.12);
            margin-bottom: 16px;
        }

        /* КАЛЕНДАРЬ */
        .calendar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
            margin-bottom: 12px;
        }

        .calendar-legend {
            display: flex;
            gap: 12px;
            font-size: 12px;
            margin-bottom: 14px;
            background: #FAFAFA;
            padding: 8px 12px;
            border-radius: 8px;
            color: var(--text-muted);
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 6px;
            text-align: center;
        }

        .day-name {
            font-weight: 600;
            font-size: 12px;
            color: var(--text-muted);
            padding-bottom: 4px;
        }

        .day-cell {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .day-cell.available {
            background-color: var(--green-available);
            color: var(--green-text);
            border: 1px solid #A5D6A7;
            font-weight: 600;
        }

        .day-cell.disabled {
            background-color: var(--disabled-gray);
            color: #C0C0C0;
            cursor: not-allowed;
        }

        .day-cell.selected {
            background-color: var(--accent-pink) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba(255, 133, 161, 0.4);
        }

        /* СЕТКА ВРЕМЕНИ */
        .time-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 10px;
        }

        .time-slot {
            padding: 10px;
            text-align: center;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
        }

        .time-slot.selected {
            background: var(--accent-pink);
            color: white;
            border-color: var(--accent-pink);
        }

        .btn-submit {
            width: 100%;
            background: var(--accent-pink);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 16px;
        }

        .btn-submit:disabled {
            background: #CCCCCC;
        }
    </style>
</head>
<body>

<div class="container">
    <h2>✨ Запись в Сахарок_nails</h2>

    <!-- Шаг 1: Услуга -->
    <div class="card">
        <label><b>1. Выберите услугу:</b></label>
        <select id="serviceSelect" style="width:100%; padding:10px; margin-top:8px; border-radius:8px;">
            <option value="Маникюр + Гель-лак">Маникюр + Гель-лак (2 200 ₽)</option>
            <option value="Наращивание ногтей">Наращивание ногтей (3 500 ₽)</option>
            <option value="Снятие + Гигиена">Снятие + Гигиена (1 200 ₽)</option>
        </select>
    </div>

    <!-- Шаг 2: Календарь -->
    <div class="card">
        <div class="calendar-header">
            <span id="monthTitle">Выберите дату</span>
        </div>

        <div class="calendar-legend">
            <div class="legend-item">
                <div class="legend-dot" style="background:#A5D6A7;"></div>
                <span>Есть окна</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot" style="background:#C0C0C0;"></div>
                <span>Нет мест</span>
            </div>
        </div>

        <div class="calendar-grid" id="calendarGrid"></div>
    </div>

    <!-- Шаг 3: Выбор времени -->
    <div class="card" id="timeSection" style="display:none;">
        <label><b>3. Доступное время на <span id="selectedDateText"></span>:</b></label>
        <div class="time-grid" id="timeGrid"></div>
    </div>

    <!-- Шаг 4: Контакты -->
    <div class="card">
        <label><b>4. Ваши контакты:</b></label>
        <input type="text" id="clientName" placeholder="Ваше имя" style="width:90%; padding:10px; margin-top:8px; margin-bottom:8px; border-radius:8px; border:1px solid #ddd;">
        <input type="text" id="clientPhone" placeholder="Номер телефона (+7...)" style="width:90%; padding:10px; border-radius:8px; border:1px solid #ddd;">
    </div>

    <button class="btn-submit" id="submitBtn" onclick="sendBooking()" disabled>Подтвердить запись</button>

    <!-- Плашка отмены записи -->
    <div class="info-box" style="background: #FFF8F9; border: 1px dashed var(--accent-pink); border-radius: 14px; padding: 14px; font-size: 13px; color: var(--text-dark); line-height: 1.5; margin-top: 16px;">
        💬 <b>Нужно перенести или отменить запись?</b><br>
        Напишите нашему Telegram-боту или свяжитесь с администратором.
    </div>
</div>

<script>
    const tg = window.Telegram?.WebApp;
    if (tg) tg.expand();

    let availableDates = [];
    let selectedDate = null;
    let selectedTime = null;

    async function loadAvailableDates() {
        try {
            const res = await fetch("/api/available-dates");
            const data = await res.json();
            availableDates = data.dates || [];
            renderCalendar();
        } catch (err) {
            console.error("Ошибка загрузки дат:", err);
        }
    }

    function renderCalendar() {
        const grid = document.getElementById("calendarGrid");
        grid.innerHTML = `
            <div class="day-name">Пн</div><div class="day-name">Вт</div><div class="day-name">Ср</div>
            <div class="day-name">Чт</div><div class="day-name">Пт</div><div class="day-name">Сб</div><div class="day-name">Вс</div>
        `;

        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();

        const daysInMonth = new Date(year, month + 1, 0).getDate();

        for (let i = 1; i <= daysInMonth; i++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
            const dayEl = document.createElement("div");
            dayEl.classList.add("day-cell");
            dayEl.innerText = i;

            if (availableDates.includes(dateStr)) {
                dayEl.classList.add("available");
                dayEl.onclick = () => selectDate(dateStr, dayEl);
            } else {
                dayEl.classList.add("disabled");
            }

            grid.appendChild(dayEl);
        }
    }

    async function selectDate(dateStr, element) {
        document.querySelectorAll(".day-cell").forEach(el => el.classList.remove("selected"));
        element.classList.add("selected");
        
        selectedDate = dateStr;
        selectedTime = null;
        checkValidation();

        const [y, m, d] = dateStr.split('-');
        document.getElementById("selectedDateText").innerText = `${d}.${m}.${y}`;
        document.getElementById("timeSection").style.display = "block";
        
        await loadTimeSlots(dateStr);
    }

    async function loadTimeSlots(dateStr) {
        const grid = document.getElementById("timeGrid");
        grid.innerHTML = "<small style='color:var(--text-muted)'>Загрузка...</small>";

        const res = await fetch(`/api/slots?date=${dateStr}`);
        const data = await res.json();
        grid.innerHTML = "";

        if (!data.slots || data.slots.length === 0) {
            grid.innerHTML = "<small style='color:var(--text-muted)'>Нет свободных окон</small>";
            return;
        }

        data.slots.forEach(slot => {
            const btn = document.createElement("div");
            btn.classList.add("time-slot");
            btn.innerText = slot;
            btn.onclick = () => {
                document.querySelectorAll(".time-slot").forEach(el => el.classList.remove("selected"));
                btn.classList.add("selected");
                selectedTime = slot;
                checkValidation();
            };
            grid.appendChild(btn);
        });
    }

    function checkValidation() {
        const name = document.getElementById("clientName").value.trim();
        const phone = document.getElementById("clientPhone").value.trim();
        document.getElementById("submitBtn").disabled = !(selectedDate && selectedTime && name && phone);
    }

    document.getElementById("clientName").addEventListener("input", checkValidation);
    document.getElementById("clientPhone").addEventListener("input", checkValidation);

    async function sendBooking() {
        const payload = {
            service_name: document.getElementById("serviceSelect").value,
            price: document.getElementById("serviceSelect").value.includes("Наращивание") ? 3500 : 2200,
            date: selectedDate,
            time: selectedTime,
            user_name: document.getElementById("clientName").value,
            phone: document.getElementById("clientPhone").value,
            telegram_username: tg?.initDataUnsafe?.user?.username ? `@${tg.initDataUnsafe.user.username}` : "@customer"
        };

        const res = await fetch("/api/book", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("✨ Запись успешно создана!");
            if (tg) tg.close();
            location.reload();
        } else {
            const err = await res.json();
            alert("❌ " + (err.detail || "Ошибка при бронировании."));
        }
    }

    loadAvailableDates();
</script>
</body>
</html>
