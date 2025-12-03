import os
import time
from contextlib import asynccontextmanager
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from handlers import setup_handlers
from services.hh_service import send_daily_vacancies

load_dotenv()

bot: Bot | None = None
dp: Dispatcher | None = None
scheduler: AsyncIOScheduler | None = None


async def set_webhook(bot_instance: Bot, webhook_url: str):
    """Устанавливает webhook для Telegram"""
    await bot_instance.delete_webhook(drop_pending_updates=True)
    time.sleep(0.5)
    await bot_instance.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types()
    )
    print(f"✅ Webhook установлен: {webhook_url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, scheduler

    # --- STARTUP ---
    token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")

    if not token:
        raise RuntimeError("❌ BOT_TOKEN не задан в переменных окружения!")

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    setup_handlers(dp)

    # Устанавливаем webhook, если указан URL
    if webhook_url:
        await set_webhook(bot, webhook_url)
    else:
        raise RuntimeError("❌ WEBHOOK_URL не задан! Для Render он обязателен.")

    # Запускаем планировщик (рассылка в 9:00)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_vacancies, CronTrigger(hour=9, minute=0), args=[bot])
    scheduler.start()
    print("🗓️ Планировщик запущен (ежедневная рассылка в 9:00)")

    yield  # ← Приложение работает

    # --- SHUTDOWN ---
    print("⏹️ Остановка...")
    if scheduler:
        scheduler.shutdown(wait=False)
    if bot:
        await bot.session.close()
    print("✅ Бот остановлен")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health():
    """Проверка, что бот жив"""
    return {"status": "✅ Бот работает!", "webhook": os.getenv("WEBHOOK_URL")}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Принимает обновления от Telegram"""
    if not bot or not dp:
        return {"error": "Бот не инициализирован"}
    
    update_data: dict[str, Any] = await request.json()
    update = Update.model_validate(update_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
