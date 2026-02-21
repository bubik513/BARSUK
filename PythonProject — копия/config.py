import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем переменные окружения из файла .env в корне проекта
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class Config:
    # Токен Telegram-бота
    BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

    # Проверка наличия токена
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не найден в .env файле!")

    # Настройки PostgreSQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "barsuk_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")