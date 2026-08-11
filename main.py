#!/usr/bin/env python3
import os
import datetime
import json
import logging
import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiohttp import web
from aiogram import Bot, Dispatcher, F, BaseMiddleware, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message, CallbackQuery, TelegramObject, FSInputFile
from redis.asyncio import Redis

# Импорт ваших модулей
import config
from db import execute_query
from creator_menu import router as admin_router
from keyboards import (
    start_key, deposit_key, main_keyboard, set_comands, subscr_key,
    tarifs_key, method_keys, profile_key, method_keys_menu,
    next_key, back_fter_pay_key
)
from languages import main_menu, activate_button, tarifs, subscribe, profile
from payments import router as pay_router

# 1. Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis и Bot
redis_url = os.getenv("REDIS_URL")

if not redis_url:
    redis_host = os.getenv("REDIS_HOST", "redis.railway.internal")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_password = os.getenv("REDIS_PASSWORD", None)

    if redis_password:
        redis_url = f"redis://default:{redis_password}@{redis_host}:{redis_port}/0"
    else:
        redis_url = f"redis://{redis_host}:{redis_port}/0"

if not redis_url.startswith(("redis://", "rediss://", "unix://")):
    redis_url = f"redis://{redis_url}"

redis_client = Redis.from_url(redis_url)
storage = RedisStorage.from_url(redis_url)

BOT_TOKEN = config.token
WEBHOOK_PATH_CRYPTOBOT = '/369546:AAxPmfahjiLrKIIgDNzwLtkhtlVjtIl1SPi'
WEBHOOK_CRISTAL_PAY = '/cristal_pay'
WEBHOOK_CIS_PAY = '/cis_pay'

bot: Bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
router = Router()

# --- Middleware ---
class BlacklistMiddleware(BaseMiddleware):
    def __init__(self, db_path: str):
        self.db_path = db_path
        super().__init__()

    async def is_user_blacklisted(self, user_id: int) -> bool:
        query = 'SELECT * FROM black_list WHERE user_id = ?'
        result = await execute_query(query, (user_id,), False, 1)
        return result is not None

    async def __call__(self, handler, event: TelegramObject, data: Dict[str, Any]) -> Any:
        user_id = event.from_user.id if isinstance(event, (Message, CallbackQuery)) else None
        if user_id and await self.is_user_blacklisted(user_id):
            return
        return await handler(event, data)

# --- Функции логики ---
async def update_sub_cryptobot(user_id, amount, bot: Bot):
    now = datetime.datetime.now()
    days_to_add = 30 if int(amount) == 99 else (180 if int(amount) == 499 else 365)
    new_end_date = now + datetime.timedelta(days=days_to_add)
    
    update_query = 'UPDATE users SET date_end_sub = ?, sub_name = ? WHERE user_id = ?'
    await execute_query(update_query, (new_end_date.strftime("%Y-%m-%d %H:%M:%S"), 'month', user_id), True, 0)
    await bot.send_message(user_id, "✅ Подписка успешно продлена!")
    await bot.send_message(chat_id=config.stats_id, text=f'💰 Пользователь {user_id} совершил платеж на {amount}$')

async def handle_postback(request):
    body = await request.text()
    data = json.loads(body)
    if request.path == WEBHOOK_PATH_CRYPTOBOT:
        invoice = data.get('payload', {})
        user_id = await execute_query('SELECT user_id FROM users WHERE invoice_id = ?', (int(invoice.get('invoice_id')),), False, 1)
        if user_id: await update_sub_cryptobot(user_id[0], invoice.get('amount'), bot)
    return web.Response(text="OK", status=200)

# --- Хендлеры ---
@router.message(F.text == '/start')
async def get_welcome(message: Message, bot: Bot):
    await set_comands(bot)
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    # Регистрация пользователя с правильными параметрами вызова
    await execute_query(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username),
        True,
        0
    )
    
    # Отправляем сообщение с клавиатурой
    await bot.send_message(
        user_id, 
        "Добро пожаловать!", 
        reply_markup=main_keyboard
    )

# --- Запуск ---
async def main():
    dp = Dispatcher(storage=storage)
    dp.message.middleware(BlacklistMiddleware(db_path='database.db'))
    dp.callback_query.middleware(BlacklistMiddleware(db_path='database.db'))

    dp.include_router(router)
    dp.include_router(admin_router)
    dp.include_router(pay_router)

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH_CRYPTOBOT, handle_postback)
    app.router.add_post(WEBHOOK_CIS_PAY, handle_postback)
    app.router.add_post(WEBHOOK_CRISTAL_PAY, handle_postback)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 3002))
    site = web.TCPSite(runner, '0.0.0.0', port)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"Веб-сервер на порту {port}. Запуск Polling...")

    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
