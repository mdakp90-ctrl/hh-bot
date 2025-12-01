import os

import asyncpg
from dotenv import load_dotenv

# Цвета ANSI
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# Символы для Windows-совместимости
SUCCESS = "[OK]"
ERROR = "[ERROR]"

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def init_db():
    if not DATABASE_URL:
        print(f"{RED}{ERROR} DATABASE_URL не задан в .env{RESET}")
        return False

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                full_name TEXT,
                city TEXT,
                desired_position TEXT,
                skills TEXT,
                resume TEXT
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS search_filters (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                position TEXT,
                city TEXT,
                salary_from INTEGER,
                remote BOOLEAN,
                metro TEXT,
                freshness_days INTEGER CHECK (freshness_days BETWEEN 1 AND 3),
                employment TEXT,
                experience TEXT,
                only_direct_employers BOOLEAN
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS llm_settings (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                base_url TEXT DEFAULT 'https://api.openai.com/v1',
                api_key TEXT,
                model TEXT DEFAULT 'gpt-4o-mini'
            )
        ''')
        await conn.close()
        print(f"{GREEN}{SUCCESS} Таблицы users, search_filters и llm_settings готовы{RESET}")
        return True
    except Exception as e:
        print(f"{RED}{ERROR} Ошибка подключения к БД: {e}{RESET}")
        return False