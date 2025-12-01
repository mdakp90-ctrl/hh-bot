from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/profile"), KeyboardButton(text="/search_settings")],
            [KeyboardButton(text="/vacancies")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )