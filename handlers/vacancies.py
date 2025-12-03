from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from db.models import get_search_filters
from services.hh_service import fetch_vacancies

# Глобальное хранилище состояния (можно заменить на FSM или Redis)
user_pages = {}

# --- Функция получения вакансий с HH.ru ---
async def get_vacancies_from_hh(user_id=None):
    
    # Подготовим фильтры для получения вакансий
    filters = {
        "position": "QA",  # жестко задано по умолчанию
        "per_page": 5  # Обновлено, так как теперь per_page задается в сервисе
    }
    
    # Если передан user_id, получаем фильтры из базы данных
    if user_id:
        user_filters = await get_search_filters(user_id)
        if user_filters:
            # Обновляем фильтры из базы данных
            if user_filters.get("position"):
                filters["position"] = user_filters["position"]
            if user_filters.get("city"):
                filters["city"] = user_filters["city"]
            if user_filters.get("salary_from"):
                filters["salary_from"] = user_filters["salary_from"]
            if user_filters.get("remote") is not None:
                filters["remote"] = user_filters["remote"]
            if user_filters.get("freshness_days"):
                filters["freshness_days"] = user_filters["freshness_days"]
            if user_filters.get("employment"):
                filters["employment"] = user_filters["employment"]
            if user_filters.get("experience"):
                filters["experience"] = user_filters["experience"]
            if user_filters.get("only_direct_employers") is not None:
                filters["only_direct_employers"] = user_filters["only_direct_employers"]

    # Удаляем ненужную проверку, т.к. она будет в обработчике команды /vacancies
    # Проверка была перемещена в обработчик команды /vacancies
    
    # Получаем вакансии через сервис
    try:
        vacancies = await fetch_vacancies(filters)
        # Ограничиваем количество вакансий до 100
        vacancies = vacancies[:100]

        return vacancies
    except Exception:
        return []

def format_vacancy(vac, vacancy_number, total_vacancies):
    vacancy_name = vac.get('name', 'Без названия')
    company_name = vac['employer'].get('name', 'Не указано')
    salary_from = vac.get('salary', {}).get('from') or 'Не указана'
    city = vac['area'].get('name', 'Не указан')
    url = vac.get('alternate_url', '#')

    message_text = (
        f"💼 <b>{vacancy_name}</b>\n"
        f"🏢 {company_name}\n"
        f"💰 От {salary_from} ₽\n"
        f"📍 {city}\n"
        f"🔗 <a href='{url}'>Подробнее</a>"
    )
    return message_text
def normalize_vacancy_for_llm(vacancy_hh: dict) -> dict:
    """
    Преобразует вакансию из формата hh.ru API в формат,
    ожидаемый LLM-сервисом (с ключами: title, company, city и т.д.).
    """
    employer = vacancy_hh.get("employer") or {}
    area = vacancy_hh.get("area") or {}
    salary = vacancy_hh.get("salary") or {}
    experience = vacancy_hh.get("experience") or {}
    employment = vacancy_hh.get("employment") or {}

    return {
        "title": vacancy_hh.get("name", "Не указано"),
        "company": employer.get("name", "Не указана"),
        "city": area.get("name", "Не указан"),
        "url": vacancy_hh.get("alternate_url", ""),
        "description": vacancy_hh.get("description", ""),
        "id": vacancy_hh.get("id"),
        "salary_from": salary.get("from"),
        "salary_to": salary.get("to"),
        "currency": salary.get("currency"),
        "experience": experience.get("name", ""),
        "employment": employment.get("name", ""),
    }

# --- Отправка страницы ---
async def send_page(message: types.Message, page_num: int, page_data = None):
    user_id = message.from_user.id if message.from_user else None
    # Если page_data не передан, получаем из user_pages
    if page_data is None:
        if user_id is None:
            await message.answer("Не удалось получить информацию о пользователе.")
            return
        page_data = user_pages.get(user_id)
        if not page_data:
            await message.answer("Данные устарели.")
            return

    vacancies = page_data['vacancies']
    total_pages = page_data['total_pages']

    PAGE_SIZE = 5
    start_idx = (page_num - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_vacancies = vacancies[start_idx:end_idx]

    # Отправляем каждую вакансию отдельным сообщением
    if not page_vacancies:
        await message.answer("🚫 На этой странице вакансий нет.", parse_mode="HTML")
    else:
        for vac in page_vacancies:
            msg_text = format_vacancy(vac, 0, 0)
            keyboard = get_vacancy_keyboard(vac["id"])
            await message.answer(msg_text, reply_markup=keyboard, parse_mode="HTML")

    # Отправляем сообщение с навигацией под всеми карточками
    nav_msg = f"📂 Страница {page_num} из {total_pages}"
    nav_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"page:{page_num - 1}" if page_num > 1 else "noop"),
            InlineKeyboardButton(text=f"{page_num}/{total_pages}", callback_data="noop"),
            InlineKeyboardButton(text="▶️ Вперёд", callback_data=f"page:{page_num + 1}" if page_num < total_pages else "noop"),
        ]
    ])
    await message.answer(nav_msg, reply_markup=nav_keyboard)


def get_vacancy_keyboard(vacancy_id: str) -> InlineKeyboardMarkup:
    """
    Кнопки под вакансией: действия
    """

    # Действия
    buttons = [
        [
            InlineKeyboardButton(text="📄 Резюме", callback_data=f"generate_resume:{vacancy_id}"),
            InlineKeyboardButton(text="✉️ Cover letter", callback_data=f"generate_cover:{vacancy_id}"),
            InlineKeyboardButton(text="❌ Неинтересно", callback_data=f"skip:{vacancy_id}")
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Обработчик команды /vacancies ---
router = Router()

@router.message(Command("vacancies"))
async def show_vacancies(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    print(f"🔍 Received /vacancies from user {user_id}")
    if not message.from_user:
        await message.answer("Не удалось получить информацию о пользователе.")
        return
    if not message.chat:
        await message.answer("Не удалось получить информацию о чате.")
        return
    chat_id = message.chat.id

    # Получаем фильтры пользователя
    try:
        user_filters = await get_search_filters(user_id)
        if not user_filters or not user_filters.get("city"):
            print(f"⚠️ City not specified for user {user_id}")
            await message.answer("⚠️ Город не указан. Пожалуйста, задайте его через /settings.")
            return

        # Проверяем, что город может быть преобразован в area_id
        from services.hh_service import CITY_TO_AREA_ID
        city = user_filters.get("city")
        if city is None:
            print(f"⚠️ City not specified for user {user_id}")
            await message.answer("⚠️ Город не указан. Пожалуйста, задайте его через /settings.")
            return

        area_id = CITY_TO_AREA_ID.get(city)
        if area_id is None:
            print(f"⚠️ Unsupported city '{city}' for user {user_id}")
            await message.answer(f"⚠️ Город '{city}' не поддерживается. Пожалуйста, выберите поддерживаемый город через /settings.")
            return

        # Получаем вакансии
        vacancies = await get_vacancies_from_hh(user_id)
        print(f"💼 Found {len(vacancies)} vacancies for user {user_id}")
        if not vacancies:
            await message.answer("Вакансий не найдено.")
            return

        # PAGE_SIZE = 5
        # total_pages = (len(vacancies) + PAGE_SIZE - 1) // PAGE_SIZE # ceil(100/5) = 20
        PAGE_SIZE = 5
        total_pages = (len(vacancies) + PAGE_SIZE - 1) // PAGE_SIZE # Динамически вычисляем количество страниц

        def get_page_vacancies(page_num: int):
            start = (page_num - 1) * PAGE_SIZE
            end = start + PAGE_SIZE
            return vacancies[start:end]

        # Сохраняем данные пользователя
        user_pages[user_id] = {
            'vacancies': vacancies,
            'current_page': 1,  # Меняем на 1 для 1-индексации
            'total_pages': total_pages
        }

        # Отправляем первую страницу
        await send_page(message, 1, user_pages[user_id])
    except Exception as e:
        print(f"❌ Error in /vacancies for user {user_id}: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

        
# --- Новый обработчик для навигации по страницам по заданию ---
@router.callback_query(lambda c: c.data.startswith("page:"))
async def handle_page_navigation(callback: CallbackQuery, bot: Bot):
    if not callback.data or ':' not in callback.data:
        await callback.answer("Некорректные данные.")
        return
        
    try:
        page_num = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("Некорректный номер страницы.")
        return

    user_id = callback.from_user.id
    page_data = user_pages.get(user_id)
    if not page_data:
        await callback.answer("Данные устарели.")
        return

    # Проверяем, что страница в допустимом диапазоне
    if page_num < 1 or page_num > page_data['total_pages']:
        await callback.answer("Некорректный номер страницы.")
        return

    # Обновляем текущую страницу
    page_data['current_page'] = page_num
    
    # Отправляем страницу с вакансиями заново
    if callback.message:
        if isinstance(callback.message, types.Message):
            await send_page(callback.message, page_num, page_data)
    await callback.answer()

# --- Обработчики кнопок навигации по вакансиям ---
@router.callback_query(lambda c: c.data.startswith("prev:"))
async def prev_vacancy(callback: CallbackQuery, bot: Bot):
    if not callback.data or ':' not in callback.data:
        await callback.answer("Некорректные данные.")
        return
        
    vacancy_index = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    if not callback.message or not callback.message.chat:
        await callback.answer("Не удалось получить информацию о чате.")
        return
        
    chat_id = callback.message.chat.id

    page_data = user_pages.get(user_id)
    if not page_data:
        await callback.answer("Данные устарели.")
        return

    # Обновляем текущую страницу для отображения нужной вакансии
    vacancies = page_data['vacancies']
    PAGE_SIZE = 5
    start_idx = ((vacancy_index - 1) // PAGE_SIZE) * PAGE_SIZE  # Находим стартовый индекс для страницы
    page_data['current_page'] = (start_idx // PAGE_SIZE) + 1  # Меняем на 1-индексацию

    # Отправляем страницу с вакансией
    if callback.message:
        if isinstance(callback.message, types.Message):
            await send_page(callback.message, page_data['current_page'], page_data)
    await callback.answer()


# --- Обработчики для кнопок под вакансией ---
@router.callback_query(lambda c: c.data.startswith("generate_resume:"))
async def handle_generate_resume(callback: CallbackQuery, bot: Bot):
    if not callback.data or ':' not in callback.data:
        await callback.answer("Некорректные данные.")
        return

    vacancy_id = callback.data.split(":")[1]
    
    # Получаем вакансию по ID
    vacancies_data = None
    for user_id, data in user_pages.items():
        for vacancy in data['vacancies']:
            if str(vacancy['id']) == vacancy_id:
                vacancies_data = (user_id, data, vacancy)
                break
        if vacancies_data:
            break

    if not vacancies_data:
        await callback.answer("❌ Вакансия не найдена.")
        return

    user_id, page_data, vacancy = vacancies_data

    # Получаем информацию о пользователе из базы данных
    from db.models import get_user
    user = await get_user(user_id)
    if not user:
        await callback.answer("❌ Профиль пользователя не найден. Заполните профиль через /profile.")
        return

    # Получаем настройки LLM из базы данных
    from db.models import get_llm_settings
    settings = await get_llm_settings(user_id)
    if not settings:
        await callback.answer("❌ Настройки LLM не найдены. Установите настройки через /llm_settings.")
        return

    # Генерируем резюме
    from services.llm_service import generate_resume
    normalized_vacancy = normalize_vacancy_for_llm(vacancy)
    resume = await generate_resume(normalized_vacancy, user, dict(settings))

    # Отправляем резюме пользователю
    if callback.message and callback.message.chat:
        await bot.send_message(callback.message.chat.id, f"📄 <b>Сгенерированное резюме:</b>\n\n{resume}", parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("generate_cover:"))
async def handle_generate_cover(callback: CallbackQuery, bot: Bot):
    if not callback.data or ':' not in callback.data:
        await callback.answer("Некорректные данные.")
        return

    vacancy_id = callback.data.split(":")[1]
    
    # Получаем вакансию по ID
    vacancies_data = None
    for user_id, data in user_pages.items():
        for vacancy in data['vacancies']:
            if str(vacancy['id']) == vacancy_id:
                vacancies_data = (user_id, data, vacancy)
                break
        if vacancies_data:
            break

    if not vacancies_data:
        await callback.answer("❌ Вакансия не найдена.")
        return

    user_id, page_data, vacancy = vacancies_data

    # Получаем информацию о пользователе из базы данных
    from db.models import get_user
    user = await get_user(user_id)
    if not user:
        await callback.answer("❌ Профиль пользователя не найден. Заполните профиль через /profile.")
        return

    # Получаем настройки LLM из базы данных
    from db.models import get_llm_settings
    settings = await get_llm_settings(user_id)
    if not settings:
        await callback.answer("❌ Настройки LLM не найдены. Установите настройки через /llm_settings.")
        return

    # Генерируем сопроводительное письмо
    from services.llm_service import generate_cover_letter
    normalized_vacancy = normalize_vacancy_for_llm(vacancy)
    cover_letter = await generate_cover_letter(normalized_vacancy, user, dict(settings))

    # Отправляем сопроводительное письмо пользователю
    if callback.message and callback.message.chat:
        await bot.send_message(callback.message.chat.id, f"✉️ <b>Сгенерированное сопроводительное письмо:</b>\n\n{cover_letter}", parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("skip:"))
async def handle_skip_vacancy(callback: CallbackQuery, bot: Bot):
    if not callback.data or ':' not in callback.data:
        await callback.answer("Некорректные данные.")
        return

    vacancy_id = callback.data.split(":")[1]
    
    # В текущей реализации, "Неинтересно" просто отображает сообщение
    # В будущем можно добавить логику для сохранения пропущенных вакансий
    await callback.answer("✅ Вакансия помечена как 'Неинтересно'")

@router.callback_query(lambda c: c.data.startswith("next:"))
async def next_vacancy(callback: CallbackQuery, bot: Bot):
    if not callback.data or ':' not in callback.data:
        await callback.answer("Некорректные данные.")
        return
        
    vacancy_index = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    if not callback.message or not callback.message.chat:
        await callback.answer("Не удалось получить информацию о чате.")
        return
        
    chat_id = callback.message.chat.id

    page_data = user_pages.get(user_id)
    if not page_data:
        await callback.answer("Данные устарели.")
        return

    # Обновляем текущую страницу для отображения нужной вакансии
    vacancies = page_data['vacancies']
    PAGE_SIZE = 5
    start_idx = ((vacancy_index - 1) // PAGE_SIZE) * PAGE_SIZE  # Находим стартовый индекс для страницы
    page_data['current_page'] = (start_idx // PAGE_SIZE) + 1  # Меняем на 1-индексацию

    # Отправляем страницу с вакансией
    if callback.message:
        if isinstance(callback.message, types.Message):
            await send_page(callback.message, page_data['current_page'], page_data)
    await callback.answer()
