#!/usr/bin/env python3
import asyncio
import os

import psycopg
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def check_search_filters():
    if not DATABASE_URL:
        print("DATABASE_URL не задан в .env")
        return

    try:
        # Подключаемся к базе данных
        conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
        async with conn:
            # Выполняем запрос для проверки содержимого таблицы search_filters
            rows = await conn.fetch('''
                SELECT telegram_id, position, city, salary_from, remote, metro, freshness_days, employment, experience, only_direct_employers
                FROM search_filters;
            ''')
            
            print(f"Найдено {len(rows)} записей в таблице search_filters:")
            print("telegram_id | position | city | salary_from | remote | metro | freshness_days | employment | experience | only_direct_employers")
            print("-" * 150)
            
            for row in rows:
                telegram_id = row['telegram_id']
                position = row['position'] if row['position'] else 'NULL'
                city = row['city'] if row['city'] else 'NULL'
                salary_from = row['salary_from'] if row['salary_from'] else 'NULL'
                remote = row['remote'] if row['remote'] is not None else 'NULL'
                metro = row['metro'] if row['metro'] else 'NULL'
                freshness_days = row['freshness_days'] if row['freshness_days'] else 'NULL'
                employment = row['employment'] if row['employment'] else 'NULL'
                experience = row['experience'] if row['experience'] else 'NULL'
                only_direct_employers = row['only_direct_employers'] if row['only_direct_employers'] is not None else 'NULL'
                
                # Проверяем, является ли город пустым (NULL или '')
                if not row['city'] or row['city'] == '':
                    print(f"{telegram_id} | {position} | {city} | {salary_from} | {remote} | {metro} | {freshness_days} | {employment} | {experience} | {only_direct_employers} <- ПУСТОЙ ГОРОД")
                else:
                    print(f"{telegram_id} | {position} | {city} | {salary_from} | {remote} | {metro} | {freshness_days} | {employment} | {experience} | {only_direct_employers}")
            
            # Также выполним отдельный запрос для поиска записей с пустыми городами
            empty_city_rows = await conn.fetch('''
                SELECT telegram_id, position, city
                FROM search_filters
                WHERE city IS NULL OR city = '';
            ''')
            
            print(f"\nНайдено {len(empty_city_rows)} записей с пустым городом:")
            if empty_city_rows:
                for row in empty_city_rows:
                    print(f"telegram_id: {row['telegram_id']}, position: {row['position'] or 'NULL'}, city: {row['city'] or 'NULL'}")
            else:
                print("Нет записей с пустым городом")
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")

if __name__ == "__main__":
    asyncio.run(check_search_filters())