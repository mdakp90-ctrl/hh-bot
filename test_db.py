import asyncio
import asyncpg
from urllib.parse import urlparse

# Укажите ваш реальный URL
DATABASE_URL = "postgresql://postgres:ProjectHH@db.dsuiaexiyrcbuqjmzdby.supabase.co:5432/postgres"

parsed = urlparse(DATABASE_URL)
print("🔍 Разбор URL:")
print(f"  Хост: {parsed.hostname}")
print(f"  Порт: {parsed.port or 5432}")
print(f"  Пользователь: {parsed.username}")
print(f"  База: {parsed.path[1:]}")

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],
        )
        print("✅ Подключение к Supabase успешно!")
        await conn.close()
    except Exception as e:
        print("❌ Ошибка подключения:", e)

if __name__ == "__main__":
    asyncio.run(test_connection())