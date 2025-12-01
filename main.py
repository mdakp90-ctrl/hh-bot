import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from db.database import init_db
from handlers.llm_settings import router as llm_router
from handlers.profile import router as profile_router
from handlers.search_settings import router as search_router
from handlers.start import router as start_router
from handlers.user_registration import router as user_registration_router
from handlers.vacancies import router as vacancies_router

# Цвета ANSI
GREEN = "\033[92m"
RED = "\03[91m"
RESET = "\033[0m"

# Символы для Windows-совместимости
SUCCESS = "[OK]"
ERROR = "[ERROR]"

load_dotenv()
BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""
if not BOT_TOKEN:
    print(f"{RED}{ERROR} BOT_TOKEN не задан в .env{RESET}")
    raise ValueError("❌ BOT_TOKEN не задан в .env")

logging.basicConfig(level=logging.INFO)

async def main():
    print(f"{GREEN}{SUCCESS} Инициализация базы данных...{RESET}")
    if not await init_db():
        print(f"{RED}{ERROR} Не удалось инициализировать базу данных{RESET}")
        return
    
    print(f"{GREEN}{SUCCESS} Создание бота...{RESET}")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start_router)
    dp.include_router(user_registration_router)
    dp.include_router(profile_router)
    dp.include_router(search_router)
    dp.include_router(vacancies_router)
    dp.include_router(llm_router)
    
    print(f"{GREEN}{SUCCESS} Бот запущен!{RESET}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

def create_vacancy_card(vacancy, page_num, total_pages):
    """
    Формирует текст карточки вакансии и клавиатуру.
    vacancy: словарь с данными вакансии.
    page_num: текущая страница.
    total_pages: общее количество страниц.
    """

    # Формируем текст карточки
    title = vacancy.get('name', 'Не указано')
    employer = vacancy.get('employer', {}).get('name', 'Не указана')
    area = vacancy.get('area', {}).get('name', 'Не указан')
    salary = vacancy.get('salary')

    # Формируем строку зарплаты
    if salary and salary.get('from'):
        salary_str = f"от {salary['from']} {'руб.' if salary.get('currency') == 'RUR' else salary.get('currency', '')}"
    elif salary and salary.get('to'):
        salary_str = f"до {salary['to']} {'руб.' if salary.get('currency') == 'RUR' else salary.get('currency', '')}"
    else:
        salary_str = "-"

    # Формируем текст сообщения
    text = (
        f"💼 {title}\n"
        f"🏢 {employer}\n"
        f"📍 {area}\n"
        f"💰 {salary_str}\n"
        f"[Открыть]({vacancy.get('alternate_url', '#')})"
    )

    # Создаем клавиатуру для одной вакансии
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 Резюме", callback_data=f"resume_{vacancy.get('id')}"),
        InlineKeyboardButton(text="✉️ Cover letter", callback_data=f"cover_{vacancy.get('id')}"),
        InlineKeyboardButton(text="❌ Неинтересно", callback_data=f"skip_{vacancy.get('id')}")
    )

    # Добавляем навигацию внизу (если нужно, можно сделать отдельным сообщением)
    # Но в вашем случае, судя по изображению, навигация отдельно
    nav_builder = InlineKeyboardBuilder()
    nav_builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"prev_{page_num}"),
        InlineKeyboardButton(text=f"{page_num}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton(text="▶️ Вперёд", callback_data=f"next_{page_num}")
    )

    return text, builder.as_markup(), nav_builder.as_markup()