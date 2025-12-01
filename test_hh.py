import asyncio

from services.hh_service import fetch_vacancies


async def test():
    filters = {
        "position": "Python",
        "city": "Москва",
        "salary_from": 100000,
        "remote": False,
        "freshness_days": 1,
        "employment": "full",
        "experience": "between1And3",
        "only_direct_employers": False
    }
    vacancies = await fetch_vacancies(filters)
    print(f"Найдено: {len(vacancies)} вакансий")
    for v in vacancies[:2]:
        print(v["title"], v["company"], v["url"])

asyncio.run(test())