import subprocess
import time

# Запускаем FastAPI веб-сервер
server_process = subprocess.Popen(["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"])

# Запускаем Telegram-бота
bot_process = subprocess.Popen(["python", "bot.py"])

try:
    server_process.wait()
    bot_process.wait()
except KeyboardInterrupt:
    server_process.terminate()
    bot_process.terminate()