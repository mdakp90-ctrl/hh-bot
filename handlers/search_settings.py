from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from db.models import upsert_search_filter

router = Router()

class SearchSettings(StatesGroup):
    position = State()
    city = State()
    salary_from = State()
    work_type = State()
    metro = State()
    freshness = State()
    employment = State()
    experience = State()
    agency_vacancies = State()

def work_type_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Удалёнка")],
            [KeyboardButton(text="Офис")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def employment_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Полная")],
            [KeyboardButton(text="Частичная")],
            [KeyboardButton(text="Удалённая")],
            [KeyboardButton(text="Проектная")],
            [KeyboardButton(text="Стажировка")],
            [KeyboardButton(text="Волонтёрство")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def experience_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нет опыта")],
            [KeyboardButton(text="1–3 года")],
            [KeyboardButton(text="3–6 лет")],
            [KeyboardButton(text="Более 6 лет")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def yes_no_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ДА")],
            [KeyboardButton(text="НЕТ")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def city_kb():
    cities = [
        "Москва",
        "Санкт-Петербург",
        "Новосибирск",
        "Екатеринбург",
        "Казань",
        "Нижний Новгород",
        "Челябинск",
        "Самара",
        "Омск",
        "Ростов-на-Дону",
        "Уфа",
        "Красноярск",
        "Воронеж",
        "Пермь",
        "Волгоград"
    ]
    # Группируем по 2 кнопки в строке
    keyboard = [
        [KeyboardButton(text=cities[i]), KeyboardButton(text=cities[i+1]) if i+1 < len(cities) else KeyboardButton(text="")]
        for i in range(0, len(cities), 2)
    ]
    # Убираем пустые кнопки
    cleaned_keyboard = []
    for row in keyboard:
        cleaned_row = [btn for btn in row if btn.text]
        if cleaned_row:
            cleaned_keyboard.append(cleaned_row)

    return ReplyKeyboardMarkup(
        keyboard=cleaned_keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )

@router.message(F.text == "/search_settings")
async def cmd_search_settings(message: types.Message, state: FSMContext):
    await message.answer("💼 Укажите желаемую должность:")
    await state.set_state(SearchSettings.position)

@router.message(SearchSettings.position)
async def process_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text or "")
    await message.answer("🏙️ Выберите город поиска:", reply_markup=city_kb())
    await state.set_state(SearchSettings.city)

@router.message(SearchSettings.city)
async def process_city(message: types.Message, state: FSMContext):
    from services.hh_service import CITY_TO_AREA_ID  # Импортируем справочник городов
    
    city = message.text or ""
    # Проверяем, поддерживается ли город
    if city and city not in CITY_TO_AREA_ID:
        # Показываем список поддерживаемых городов
        supported_cities = list(CITY_TO_AREA_ID.keys())
        cities_list = ', '.join(supported_cities)
        await message.answer(f"❌ Город '{city}' не поддерживается. Выберите один из поддерживаемых городов:\n{cities_list}")
        await state.set_state(SearchSettings.city)  # Остаемся в том же состоянии
        return
    
    await state.update_data(city=city)
    await message.answer("💰 Мин. зарплата (в рублях, число):", reply_markup=None)
    await state.set_state(SearchSettings.salary_from)

@router.message(SearchSettings.salary_from)
async def process_salary(message: types.Message, state: FSMContext):
    if message.text and message.text.isdigit():
        await state.update_data(salary_from=int(message.text))
    else:
        await state.update_data(salary_from=0)
    await message.answer("📍 Формат работы:", reply_markup=work_type_kb())
    await state.set_state(SearchSettings.work_type)

@router.message(SearchSettings.work_type)
async def process_work_type(message: types.Message, state: FSMContext):
    if message.text == "Удалёнка":
        await state.update_data(remote=True, metro=None)
        await message.answer("📅 Свежесть вакансий (1, 2 или 3 дня):", reply_markup=None)
    elif message.text == "Офис":
        await state.update_data(remote=False)
        await message.answer("🚇 Укажите ближайшие станции метро (через запятую):", reply_markup=None)
        await state.set_state(SearchSettings.metro)
        return
    else:
        await message.answer("📍 Формат работы:", reply_markup=work_type_kb())
        return
    await state.set_state(SearchSettings.freshness)

@router.message(SearchSettings.metro)
async def process_metro(message: types.Message, state: FSMContext):
    await state.update_data(metro=message.text or "")
    await message.answer("📅 Свежесть вакансий (1, 2 или 3 дня):")
    await state.set_state(SearchSettings.freshness)

@router.message(SearchSettings.freshness)
async def process_freshness(message: types.Message, state: FSMContext):
    if message.text in ("1", "2", "3"):
        await state.update_data(freshness_days=int(message.text))
    else:
        await state.update_data(freshness_days=1)
    await message.answer("👔 Тип занятости:", reply_markup=employment_kb())
    await state.set_state(SearchSettings.employment)

@router.message(SearchSettings.employment)
async def process_employment(message: types.Message, state: FSMContext):
    mapping = {
        "Полная": "full",
        "Частичная": "part",
        "Удалённая": "remote",
        "Проектная": "project",
        "Стажировка": "probation",
        "Волонтёрство": "volunteer"
    }
    text = message.text
    if text is not None:
        emp = mapping.get(text)
        if emp:
            await state.update_data(employment=emp)
        else:
            await state.update_data(employment="full")
    else:
        await state.update_data(employment="full")
    await message.answer("🧳 Опыт работы:", reply_markup=experience_kb())
    await state.set_state(SearchSettings.experience)

@router.message(SearchSettings.experience)
async def process_experience(message: types.Message, state: FSMContext):
    mapping = {
        "Нет опыта": "noExperience",
        "1–3 года": "between1And3",
        "3–6 лет": "between3And6",
        "Более 6 лет": "moreThan6"
    }
    text = message.text
    if text is not None:
        exp = mapping.get(text)
        if exp:
            await state.update_data(experience=exp)
        else:
            await state.update_data(experience="noExperience")
    else:
        await state.update_data(experience="noExperience")
    await message.answer("🏢 Показывать вакансии агентств?", reply_markup=yes_no_kb())
    await state.set_state(SearchSettings.agency_vacancies)

@router.message(SearchSettings.agency_vacancies)
async def process_agency_vacancies(message: types.Message, state: FSMContext):
    text = (message.text or "").strip().upper()
    if text not in ("ДА", "НЕТ"):
        await message.answer("Пожалуйста, выберите:", reply_markup=yes_no_kb())
        return

    # Если "НЕТ" → только прямые работодатели
    only_direct = (text == "НЕТ")
    await state.update_data(only_direct_employers=only_direct)

    # Сохраняем всё
    data = await state.get_data()
    user_id = message.from_user.id
    if user_id is None:
        await message.answer("❌ Не удалось получить ID пользователя")
        return
        
    data["telegram_id"] = user_id
    await upsert_search_filter(user_id, data)

    from keyboards.main_menu import get_main_menu
    await message.answer("✅ Фильтры поиска сохранены!", reply_markup=get_main_menu())
    await state.clear()