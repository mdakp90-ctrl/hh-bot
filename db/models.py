import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Используем чистый URL: postgresql://...
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL не задан в .env")

# Убираем любую подмену URL — asyncpg работает с postgresql:// напрямую


async def create_or_update_user(data):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO users (telegram_id, full_name, city, desired_position, skills, resume)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (telegram_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                city = EXCLUDED.city,
                desired_position = EXCLUDED.desired_position,
                skills = EXCLUDED.skills,
                resume = EXCLUDED.resume
        """, data["telegram_id"], data.get("full_name"), data.get("city"),
           data.get("desired_position"), data.get("skills"), data.get("resume"))
    finally:
        await conn.close()


async def get_user(tid):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", tid)
        return dict(row) if row else None
    finally:
        await conn.close()


async def upsert_search_filter(tid, data):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO search_filters (
                telegram_id, position, city, salary_from, remote, metro,
                freshness_days, employment, experience, only_direct_employers
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (telegram_id) DO UPDATE SET
                position = EXCLUDED.position,
                city = EXCLUDED.city,
                salary_from = EXCLUDED.salary_from,
                remote = EXCLUDED.remote,
                metro = EXCLUDED.metro,
                freshness_days = EXCLUDED.freshness_days,
                employment = EXCLUDED.employment,
                experience = EXCLUDED.experience,
                only_direct_employers = EXCLUDED.only_direct_employers
        """, tid, data.get("position"), data.get("city"), data.get("salary_from"),
           data.get("remote"), data.get("metro"), data.get("freshness_days"),
           data.get("employment"), data.get("experience"), data.get("only_direct_employers"))
    finally:
        await conn.close()


async def get_search_filters(tid):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT * FROM search_filters WHERE telegram_id = $1", tid)
        return dict(row) if row else None
    finally:
        await conn.close()


async def upsert_llm_settings(telegram_id: int, data: dict):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            INSERT INTO llm_settings (telegram_id, base_url, api_key, model)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                base_url = EXCLUDED.base_url,
                api_key = EXCLUDED.api_key,
                model = EXCLUDED.model
        """, telegram_id, data.get("base_url"), data.get("api_key", ""), data.get("model"))
    finally:
        await conn.close()


async def get_llm_settings(telegram_id: int):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT * FROM llm_settings WHERE telegram_id = $1", telegram_id)
        return dict(row) if row else None
    finally:
        await conn.close()