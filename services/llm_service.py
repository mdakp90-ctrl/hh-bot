# services/llm_service.py
import httpx
from typing import Dict, Any

async def generate_resume(vacancy: Dict[str, Any], user: Dict[str, Any], settings: Dict[str, Any]) -> str:
    prompt = f"""
Роль: эксперт по трудоустройству.
Задача: создать профессиональное резюме на русском языке для кандидата под вакансию.

Вакансия:
- Название: {vacancy['title']}
- Компания: {vacancy['company']}
- Город: {vacancy['city']}
- Зарплата: {vacancy.get('salary_from', 'не указана')} – {vacancy.get('salary_to', 'не указана')}

Профиль кандидата:
- ФИО: {user.get('full_name', '—')}
- Город: {user.get('city', '—')}
- Желаемая должность: {user.get('desired_position', '—')}
- Навыки: {user.get('skills', '—')}
- Опыт: {user.get('resume', '—')}

Требования:
- Только резюме, без пояснений.
- Используй структуру: Контакты, Цель, Опыт работы, Навыки, Образование.
- Адаптируй под вакансию.
"""
    return await _call_llm(prompt, settings)

async def generate_cover_letter(vacancy: Dict[str, Any], user: Dict[str, Any], settings: Dict[str, Any]) -> str:
    prompt = f"""
Роль: соискатель высокой квалификации.
Задача: написать сопроводительное письмо на русском для вакансии.

Вакансия: {vacancy['title']} в компании {vacancy['company']} ({vacancy['city']}).

Профиль:
- Имя: {user.get('full_name', '—')}
- Навыки: {user.get('skills', '—')}

Правила:
- Письмо должно быть кратким (5–7 предложений), убедительным, без шаблонных фраз.
- Подчеркни соответствие навыков требованиям вакансии.
- Не пиши «Уважаемая HR-команда» — начни сразу с сути.
- Только текст письма, без подписи и приветствия.
"""
    return await _call_llm(prompt, settings)

async def _call_llm(prompt: str, settings: Dict[str, Any]) -> str:
    base_url = settings.get("base_url") or "https://api.openai.com/v1"
    api_key = settings.get("api_key")
    model = settings.get("model") or "gpt-3.5-turbo"

    if not api_key:
        return "❗ Сначала задайте LLM API-ключ через /llm_settings"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Ошибка LLM: {str(e)}"