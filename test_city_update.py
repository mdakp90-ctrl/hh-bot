#!/usr/bin/env python3
import asyncio
import os

import psycopg
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def test_city_update():
    if not DATABASE_URL:
        print("DATABASE_URL не задан в .env")
        return

    try:
        # Подключаемся к базе данных
        conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
        async with conn:
            # Проверим текущее состояние таблицы search_filters
            print("Текущее состояние таблицы search_filters:")
            rows = await conn.fetch('''
                SELECT telegram_id, position, city
                FROM search_filters;
            ''')
            
            for row in rows:
                print(f"telegram_id: {row['telegram_id']}, position: {row['position'] or 'NULL'}, city: {row['city'] or 'NULL'}")
            
            # Представим, что мы добавляем нового пользователя с telegram_id 123456789
            # и обновляем его данные в search_filters при регистрации
            test_telegram_id = 123456789
            test_city = "Москва"
            test_position = "Python Developer"
            
            print(f"\nОбновляем запись для telegram_id {test_telegram_id} с городом {test_city} и должностью {test_position}")
            
            # Сначала добавим пользователя в таблицу users
            await conn.execute("""
                INSERT INTO users (
                    telegram_id, full_name, city, desired_position
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    city = EXCLUDED.city,
                    desired_position = EXCLUDED.desired_position
            """, test_telegram_id, "Тестовый пользователь", test_city, test_position)
            
            # Выполняем upsert в таблицу search_filters
            await conn.execute("""
                INSERT INTO search_filters (
                    telegram_id, position, city
                ) VALUES ($1, $2, $3)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    position = EXCLUDED.position,
                    city = EXCLUDED.city
            """, test_telegram_id, test_position, test_city)
            
            # Проверим, что запись обновилась
            print("\nПосле обновления:")
            rows = await conn.fetch('''
                SELECT telegram_id, position, city
                FROM search_filters
                WHERE telegram_id = $1;
            ''', test_telegram_id)
            
            for row in rows:
                print(f"telegram_id: {row['telegram_id']}, position: {row['position'] or 'NULL'}, city: {row['city'] or 'NULL'}")
            
            # Также проверим, что другие записи остались без изменений
            print("\nВсе записи в таблице search_filters:")
            rows = await conn.fetch('''
                SELECT telegram_id, position, city
                FROM search_filters;
            ''')
            
            for row in rows:
                print(f"telegram_id: {row['telegram_id']}, position: {row['position'] or 'NULL'}, city: {row['city'] or 'NULL'}")
        print("\nТест успешно завершен!")
        
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")

if __name__ == "__main__":
    asyncio.run(test_city_update())