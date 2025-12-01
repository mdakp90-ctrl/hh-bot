# handlers/llm_settings.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.models import upsert_llm_settings, get_user

router = Router()

class LLMSettings(StatesGroup):
    base_url = State()
    api_key = State()
    model = State()

@router.message(F.text == "/llm_settings")
async def cmd_llm_settings(message: types.Message, state: FSMContext):
    user_id = getattr(message.from_user, 'id', None)
    if user_id:
        user = await get_user(user_id)
        if not user:
            await message.answer("❌ Сначала зарегистрируйтесь через /start")
            return

        await message.answer("🔗 Введите Base URL (например, https://api.openai.com/v1):")
        await state.set_state(LLMSettings.base_url)
    else:
        await message.answer("❌ Не удалось получить ID пользователя")

@router.message(LLMSettings.base_url)
async def process_base_url(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введите Base URL")
        return
    await state.update_data(base_url=message.text.strip())
    await message.answer("🔑 Введите API Key:")
    await state.set_state(LLMSettings.api_key)

@router.message(LLMSettings.api_key)
async def process_api_key(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введите API Key")
        return
    await state.update_data(api_key=message.text.strip())
    await message.answer("🤖 Введите название модели (например, gpt-4o-mini):")
    await state.set_state(LLMSettings.model)

@router.message(LLMSettings.model)
async def process_model(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Введите модель")
        return

    user_id = getattr(message.from_user, 'id', None)
    if user_id:
        data = await state.get_data()
        data["model"] = message.text.strip()
        data["telegram_id"] = user_id

        await upsert_llm_settings(user_id, data)
        await message.answer("✅ Настройки LLM сохранены!\nТеперь вы можете генерировать резюме и cover letter.")
        await state.clear()
    else:
        await message.answer("❌ Не удалось получить ID пользователя")