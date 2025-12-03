from aiogram import Dispatcher

from .llm_settings import router as llm_settings_router
from .profile import router as profile_router
from .search_settings import router as search_router
from .start import router as start_router
from .user_registration import router as user_registration_router
from .vacancies import router as vacancies_router


def setup_handlers(dp: Dispatcher):
    """Регистрирует все хендлеры в диспетчере"""
    dp.include_router(start_router)
    dp.include_router(user_registration_router)
    dp.include_router(profile_router)
    dp.include_router(search_router)
    dp.include_router(vacancies_router)
    dp.include_router(llm_settings_router)