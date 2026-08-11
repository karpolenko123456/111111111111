#!/usr/bin/env python3
import datetime
import random
from aiohttp import web
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, TelegramObject, Update, FSInputFile
from aiogram import Bot, Dispatcher, F, BaseMiddleware, Router
import logging
import contextlib
import asyncio
import config
from aiogram.fsm.context import FSMContext
from db import execute_query
from creator_menu import router as admin_router
from keyboards import *
from aiogram.fsm.storage.redis import RedisStorage

# Ссылка на Redis для Railway
REDIS_URL = 'redis://default:YOTJYxOsWOIyuRJSvtCTtrANUYGThsXc@redis.railway.internal:6379'
storage = RedisStorage.from_url(REDIS_URL)

BOT_TOKEN = config.token
router = Router()

class BlacklistMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id if hasattr(event, 'from_user') and event.from_user else None
        if user_id:
            query = 'SELECT * FROM black_list WHERE user_id = ?'
            res = await execute_query(query, (user_id,), False, 1)
            if res: return
        return await handler(event, data)

# --- ВСЯ ТВОЯ ЛОГИКА НИЖЕ ---

@router.message(CommandStart())
async def get_welcome(message: Message, state: FSMContext):
    await set_comands(message.bot)
    user_id = message.from_user.id
    query = 'INSERT OR IGNORE INTO users (user_id) VALUES (?)'
    await execute_query(query, (user_id,), True, 0)
    
    photo = FSInputFile('images/start.jpg')
    msg = (f'<b>Привет, {message.from_user.first_name}! 👋</b>\n\n'
           f'Для начала работы с ботом необходимо активировать доступ.')
    try:
        await message.answer_photo(photo=photo, caption=msg, reply_markup=start_key('АКТИВИРОВАТЬ'))
    except:
        await message.answer(msg, reply_markup=start_key('АКТИВИРОВАТЬ'))

@router.callback_query(F.data == 'activate_bot')
async def activate_bot(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    res = await execute_query('SELECT platform_id FROM users WHERE user_id = ?', (user_id,), False, 1)
    
    if res is None or res[0] is None or res[0] == 0:
        c_data = await execute_query('SELECT ref_link FROM creator WHERE user_id = ?', (config.admin_id,), False, 1)
        ref_link = c_data[0] if c_data else "https://pocketoption.com/register"
        msg = f'<b>Для работы с ботом необходимо зарегистрировать новый аккаунт по ссылке ниже 👇</b>'
        await call.message.edit_caption(caption=msg, reply_markup=reg_key('РЕГИСТРАЦИЯ', ref_link))
    else:
        await check_dep_logic(call, state)

# СКОПИРУЙ СЮДА ВСЕ СВОИ ФУНКЦИИ ИЗ СТАРОГО main.py (check_dep_logic, ob_pair, otc_pair и т.д.)

async def start_bot():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=storage)
    dp.update.outer_middleware(BlacklistMiddleware())
    dp.include_routers(router, admin_router)

    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 3003).start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(start_bot())
