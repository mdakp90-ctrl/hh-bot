import asyncio
import os
import time
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI

from handlers import setup_handlers
from services.hh_service import send_daily_vacancies

# Загружаем переменные окружения из файла .env
load_dotenv()

# Глобальные переменные для управления ресурсами (можно обернуть в класс, но для простоты — так)
bot: Bot | None = None
dp: Dispatcher | None = None
scheduler: AsyncIOScheduler | None = None


async def set_webhook(bot_instance: Bot):
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ WEBHOOK_URL не установлен, пропускаю установку webhook'а")
        return

    # Удаляем старый webhook (на всякий случай)
    await bot_instance.delete_webhook(drop_pending_updates=True)
    time.sleep(0.5)
    # Устанавливаем новый
    await bot_instance.set_webhook(url=webhook_url, allowed_updates=dp.resolve_used_update_types())
    print("✅ Webhook установлен на:", webhook_url)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, scheduler

    # === STARTUP ===
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is missing!")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    setup_handlers(dp)

    # Устанавливаем webhook, если указан WEBHOOK_URL
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        await set_webhook(bot)
        # В режиме webhook polling НЕ запускаем!
        polling_task = None
        print("🚀 Запущен в режиме webhook")
    else:
        # Иначе — запускаем polling
        polling_task = asyncio.create_task(dp.start_polling(bot))
        print("▶️ Starting Telegram bot polling...")

    # Планировщик запускаем в любом режиме
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_vacancies, CronTrigger(hour=9, minute=0), args=[bot])
    scheduler.start()
    print("🗓️ Daily vacancy scheduler started")

    yield

    # === SHUTDOWN ===
    print("⏹️ Shutting down...")
    if scheduler:
        scheduler.shutdown(wait=False)
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    if bot:
        await bot.session.close()

    print("✅ Shutdown complete")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health():
    return {"status": "alive", "bot": "hh-job-bot"}


# Убираем блок if __name__ == "__main__" — запуск только через uvicorn!
