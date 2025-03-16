import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройки базы данных
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "main")

# Формируем URL для подключения к базе данных
DATABASE_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# URL для Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Настройки Telegram бота
BOT_NAME = os.getenv("BOT_NAME", "WiquzixBot")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
APP_NAME = os.getenv("APP_NAME", "wiquzix") #в моем случае это название Telegram Mini App

# Внешний URL приложения
EXTERNAL_URL = os.getenv("EXTERNAL_URL") 

# Название приложения
