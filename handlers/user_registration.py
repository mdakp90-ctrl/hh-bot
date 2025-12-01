# handlers/user_registration.py
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from db.models import create_or_update_user

router = Router()

class Registration(StatesGroup):
    full_name = State()
    city = State()
    desired_position = State()
    skills = State()
    resume = State()


# Импортируем необходимые функции в начале файла

# @router.message(F.text == "/start")
# async def cmd_start(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     user = await get_user(user_id)
#
#     if user and user["full_name"]:
#         await message.answer("Вы уже зарегистрированы! Чтобы изменить профиль, отправьте /profile.")
#         await state.clear()
#     else:
#         await message.answer("👋 Добро пожаловать!\nВведите ваше ФИО:")
#         await state.set_state(Registration.full_name)
#         await state.update_data(telegram_id=user_id)

@router.message(Registration.full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip() if message.text else "")
    await message.answer("🏙️ В каком городе вы ищете работу?")
    await state.set_state(Registration.city)

@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip() if message.text else "")
    await message.answer("💼 Какая должность вас интересует?")
    await state.set_state(Registration.desired_position)

@router.message(Registration.desired_position)
async def process_position(message: Message, state: FSMContext):
    await state.update_data(desired_position=message.text.strip() if message.text else "")
    await message.answer("🛠️ Перечислите ключевые навыки (через запятую):")
    await state.set_state(Registration.skills)

@router.message(Registration.skills)
async def process_skills(message: Message, state: FSMContext):
    await state.update_data(skills=message.text.strip() if message.text else "")
    await message.answer(
        "📄 Вставьте ваше базовое резюме (или краткое описание опыта). "
        "Это поможет генерировать cover letter."
    )
    await state.set_state(Registration.resume)

@router.message(Registration.resume)
async def process_resume(message: Message, state: FSMContext):
    await state.update_data(resume=message.text.strip() if message.text else "")
    data = await state.get_data()
    await create_or_update_user(data)
    await message.answer(
        "✅ Профиль создан!\n\n"
        "Теперь вы можете:\n"
        "/search_settings — настроить фильтры поиска\n"
        "/vacancies — посмотреть вакансии"
    )
    await state.clear()