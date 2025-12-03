from typing import Any, Dict, List

import httpx

HH_API_URL = "https://api.hh.ru/vacancies"  # ← убраны лишние пробелы!

# Точный маппинг: как в кнопках → area_id
CITY_TO_AREA_ID = {
    "Москва": 1,
    "Санкт-Петербург": 2,
    "Новосибирск": 4,
    "Екатеринбург": 3,
    "Казань": 88,
    "Нижний Новгород": 66,
    "Челябинск": 104,
    "Самара": 72,
    "Омск": 68,
    "Ростов-на-Дону": 76,
    "Уфа": 99,
    "Красноярск": 54,
    "Воронеж": 26,
    "Пермь": 90,
    "Волгоград": 27,
}

import asyncio

# Добавляем импорт для кэширования
from datetime import datetime, timedelta

# Кэш для хранения результатов запросов
vacancies_cache = {}

async def fetch_vacancies(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Создаем ключ для кэша на основе фильтров
    cache_key = str(sorted(filters.items()))
    current_time = datetime.now()
    
    # Проверяем, есть ли валидный кэш для этих фильтров
    if cache_key in vacancies_cache:
        cached_time, cached_result = vacancies_cache[cache_key]
        # Кэшируем на 5 минут
        if current_time - cached_time < timedelta(minutes=5):
            return cached_result
    
    city = filters.get("city", "")
    area_id = CITY_TO_AREA_ID.get(city)
    if area_id is None:
        return []
    
    only_with_salary = bool(filters.get("salary_from"))
    
    all_vacancies = []
    page = 0
    # Ограничиваем количество вакансий до 10
    max_vacancies = 10
    while len(all_vacancies) < max_vacancies:
        params = {
            "text": filters.get("position") or "",
            "area": area_id,
            "per_page": 5,
            "page": page,
            "only_with_salary": only_with_salary,
        }

        if filters.get("salary_from"):
            params["salary"] = filters["salary_from"]

        # Остальные фильтры
        if filters.get("remote"):
            params["schedule"] = "remote"
        if filters.get("freshness_days") in (1, 2, 3):
            params["period"] = filters["freshness_days"]
        if filters.get("employment"):
            params["employment"] = filters["employment"]
        if filters.get("experience"):
            params["experience"] = filters["experience"]
        if filters.get("only_direct_employers"):
            params["employer_type"] = "direct"

        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; HH-Bot/1.0; +http://bot.example.com/bot.html)"}
            try:
                resp = await client.get(HH_API_URL, params=params, headers=headers)
                if resp.status_code == 200:
                    response_data = resp.json()
                    vacancies = response_data.get("items", [])
                    
                    # Если на странице нет вакансий, прерываем цикл
                    if not vacancies:
                        break
                    
                    # Преобразуем вакансии в нужный формат
                    for v in vacancies:
                        if len(all_vacancies) >= max_vacancies:
                            break
                        all_vacancies.append({
                            "id": v["id"],
                            "name": v["name"],
                            "employer": {
                                "name": v["employer"]["name"]
                            },
                            "area": {
                                "name": v["area"]["name"]
                            },
                            "salary": v.get("salary"),
                            "alternate_url": v["alternate_url"]
                        })
                    
                    # Проверяем, есть ли еще страницы
                    found_pages = response_data.get("pages", 0)
                    if page + 1 >= found_pages:
                        break
                    
                else:
                    # Продолжаем, даже если одна из страниц вернула ошибку
                    break
            except httpx.HTTPStatusError:
                # Продолжаем, даже если одна из страниц вернула ошибку
                break
            except httpx.RequestError:
                # Продолжаем, даже если одна из страниц вернула ошибку
                break
            except Exception:
                # Продолжаем, даже если одна из страниц вернула ошибку
                break

        # Опционально: задержка, чтобы не получить блокировку
        await asyncio.sleep(0.5)
        
        page += 1

    # Сохраняем результат в кэш
    vacancies_cache[cache_key] = (current_time, all_vacancies)
    
    return all_vacancies

async def send_daily_vacancies(bot):
    """
    Функция для ежедневной рассылки вакансий пользователям
    """
    # Заглушка для функции рассылки
    # В реальной реализации здесь будет логика получения пользователей и отправки им вакансий
    print("📧 Daily vacancies sending process started")
    # Примерная реализация:
    # 1. Получить всех пользователей, подписанных на рассылку
    # 2. Для каждого пользователя получить подходящие вакансии
    # 3. Отправить вакансии через бота
    pass