from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from db.models import create_or_update_user, get_user, upsert_search_filter

router = Router()

class ProfileEdit(StatesGroup):
    full_name = State()
    city = State()
    desired_position = State()
    skills = State()
    resume = State()

@router.message(F.text == "/profile")
async def cmd_profile(message: Message):
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        await message.answer("❌ Не удалось получить ID пользователя")
        return
    
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return
    
    profile_text = (
        "<b>👤 Ваш профиль</b>\n\n"
        f"<b>ФИО:</b> {user.get('full_name', 'Не указано')}\n"
        f"<b>Город:</b> {user.get('city', 'Не указан')}\n"
        f"<b>Должность:</b> {user.get('desired_position', 'Не указана')}\n"
        f"<b>Навыки:</b> {user.get('skills', 'Не указаны')}\n"
        f"<b>Резюме:</b> {user.get('resume', 'Не указано')}\n\n"
        "Чтобы изменить профиль, используйте команду /edit_profile"
    )
    
    await message.answer(profile_text, parse_mode="HTML")

@router.message(F.text == "/edit_profile")
async def cmd_edit_profile(message: Message, state: FSMContext):
    user_id = getattr(message.from_user, 'id', None)
    if user_id is None:
        await message.answer("❌ Не удалось получить ID пользователя")
        return
    
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return
    
    await message.answer("👋 Новое ФИО:")
    await state.set_state(ProfileEdit.full_name)
    await state.update_data(telegram_id=user_id)

@router.message(ProfileEdit.full_name)
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text or "")
    await message.answer("🏙️ Новый город:")
    await state.set_state(ProfileEdit.city)

@router.message(ProfileEdit.city)
async def process_city(message: Message, state: FSMContext):
    from services.hh_service import CITY_TO_AREA_ID  # Импортируем справочник городов
    
    city = message.text or ""
    # Проверяем, поддерживается ли город
    if city and city not in CITY_TO_AREA_ID:
        await message.answer(f"❌ Город '{city}' не поддерживается. Выберите один из поддерживаемых городов: {', '.join(CITY_TO_AREA_ID.keys())[:100]}...")
        await state.set_state(ProfileEdit.city)  # Остаемся в том же состоянии
        return
    
    await state.update_data(city=city)
    await message.answer("💼 Новая должность:")
    await state.set_state(ProfileEdit.desired_position)

@router.message(ProfileEdit.desired_position)
async def process_position(message: Message, state: FSMContext):
    await state.update_data(desired_position=message.text or "")
    await message.answer("🛠️ Новые навыки:")
    await state.set_state(ProfileEdit.skills)

@router.message(ProfileEdit.skills)
async def process_skills(message: Message, state: FSMContext):
    await state.update_data(skills=message.text or "")
    await message.answer("📄 Новое резюме:")
    await state.set_state(ProfileEdit.resume)

@router.message(ProfileEdit.resume)
async def process_resume(message: Message, state: FSMContext):
    await state.update_data(resume=message.text or "")
    data = await state.get_data()
    await create_or_update_user(data)
    
    # Также обновляем фильтры поиска, чтобы сохранить город и должность
    search_filters_data = {
        "city": data.get("city"),
        "position": data.get("desired_position")
    }
    await upsert_search_filter(data["telegram_id"], search_filters_data)
    
    await message.answer("✅ Профиль обновлён!")
    await state.clear()