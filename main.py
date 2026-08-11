#!/usr/bin/env python3
import os
import datetime
import json
import logging
import asyncio
from typing import Any, Dict

from aiohttp import web
from aiogram import Bot, Dispatcher, F, BaseMiddleware, Router
from aiogram.client.default import DefaultBotProperties
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
    next_key, back_fter_pay_key, signals_key
)
from languages import main_menu, activate_button, tarifs, subscribe, profile
from payments import router as pay_router

# 1. Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 2. Настройка Redis
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

# 3. Инициализация Бота
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

# --- Инициализация БД ---
async def init_db():
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        date_end_sub TEXT,
        sub_name TEXT,
        invoice_id INTEGER
    )
    '''
    await execute_query(create_table_query, (), True, 0)

    try:
        await execute_query('ALTER TABLE users ADD COLUMN username TEXT', (), True, 0)
    except Exception:
        pass

# --- Вспомогательные функции сборки клавиатур ---
async def get_settings_data():
    """Безопасное получение настроек из БД"""
    try:
        settings = await execute_query('SELECT * FROM settings', (), False, 1)
    except Exception:
        settings = None
    return settings

async def build_main_keyboard():
    """Собирает главную клавиатуру"""
    settings = await get_settings_data()

    is_free = settings[1] if settings and len(settings) > 1 else 0
    get_free = settings[2] if settings and len(settings) > 2 else "🎁 Бесплатно"
    is_reviews = settings[3] if settings and len(settings) > 3 else 0
    reviews_txt = settings[4] if settings and len(settings) > 4 else "Отзывы"
    url_reviews = settings[5] if settings and len(settings) > 5 else "https://t.me"
    is_help = settings[6] if settings and len(settings) > 6 else 0
    help_txt = settings[7] if settings and len(settings) > 7 else "Поддержка"
    url_help = settings[8] if settings and len(settings) > 8 else "https://t.me"
    is_btn_free = settings[9] if settings and len(settings) > 9 else 0

    signals_txt = "📊 Сигналы"
    profile_txt = "👤 Профиль"

    if isinstance(main_menu, dict):
        lang_data = main_menu.get('ru', main_menu)
        if isinstance(lang_data, dict):
            signals_txt = lang_data.get('signals', signals_txt)
            profile_txt = lang_data.get('profile', profile_txt)

    return main_keyboard(
        signals_txt,
        profile_txt,
        is_free,
        get_free,
        is_reviews,
        reviews_txt,
        url_reviews,
        is_help,
        help_txt,
        url_help,
        is_btn_free
    )

async def build_tarifs_keyboard():
    """Собирает клавиатуру тарифов"""
    settings = await get_settings_data()

    free_txt = settings[2] if settings and len(settings) > 2 else "1 день бесплатно"
    month_txt = "1 Месяц - 99$"
    six_txt = "6 Месяцев - 499$"
    year_txt = "1 Год - 799$"
    fre_ref = "Бесплатно за друга"

    if isinstance(tarifs, dict):
        lang_data = tarifs.get('ru', tarifs)
        if isinstance(lang_data, dict):
            month_txt = lang_data.get('month', month_txt)
            six_txt = lang_data.get('six', six_txt)
            year_txt = lang_data.get('year', year_txt)

    is_reviews = settings[3] if settings and len(settings) > 3 else 0
    reviews_txt = settings[4] if settings and len(settings) > 4 else "Отзывы"
    url_reviews = settings[5] if settings and len(settings) > 5 else "https://t.me"
    is_help = settings[6] if settings and len(settings) > 6 else 0
    help_txt = settings[7] if settings and len(settings) > 7 else "Поддержка"
    url_help = settings[8] if settings and len(settings) > 8 else "https://t.me"
    is_btn_free = settings[9] if settings and len(settings) > 9 else 0

    return tarifs_key(
        free_txt, month_txt, six_txt, year_txt, fre_ref,
        is_reviews, reviews_txt, url_reviews,
        is_help, help_txt, url_help, is_btn_free
    )

async def build_subscr_keyboard():
    """Собирает клавиатуру подписки при отсутствии доступа"""
    url = "https://t.me"
    btn1 = "Проверить подписку"
    btn2 = "Канал"

    if isinstance(subscribe, dict):
        lang_data = subscribe.get('ru', subscribe)
        if isinstance(lang_data, dict):
            url = lang_data.get('url', url)
            btn1 = lang_data.get('btn1', btn1)
            btn2 = lang_data.get('btn2', btn2)

    return subscr_key(url, btn1, btn2)

async def check_user_sub(user_id: int) -> bool:
    """Проверка наличия активной подписки у пользователя"""
    user = await execute_query('SELECT date_end_sub FROM users WHERE user_id = ?', (user_id,), False, 1)
    if user and user[0]:
        try:
            end_date = datetime.datetime.strptime(user[0], "%Y-%m-%d %H:%M:%S")
            if end_date > datetime.datetime.now():
                return True
        except Exception:
            pass
    return False

# --- Обработка платежей ---
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
        if user_id: 
            await update_sub_cryptobot(user_id[0], invoice.get('amount'), bot)
    return web.Response(text="OK", status=200)

# --- Хендлеры ---

# Команда /start
@router.message(F.text == '/start')
async def get_welcome(message: Message, bot: Bot):
    await set_comands(bot)
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    await execute_query(
        'INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)',
        (user_id, username),
        True,
        0
    )
    
    btn_name = "Активировать"
    text_msg = "Добро пожаловать!"
    photo_path = None

    if isinstance(activate_button, dict):
        lang_data = activate_button.get('ru', activate_button)
        if isinstance(lang_data, dict):
            btn_name = lang_data.get('name', btn_name)
            text_msg = lang_data.get('msg', text_msg)
            photo_path = lang_data.get('photo', None)

    kb = start_key(btn_name)

    if photo_path and os.path.exists(photo_path):
        await bot.send_photo(
            chat_id=user_id,
            photo=FSInputFile(photo_path),
            caption=text_msg,
            reply_markup=kb
        )
    else:
        await bot.send_message(
            chat_id=user_id,
            text=text_msg,
            reply_markup=kb
        )

# Нажатие кнопки "Активировать"
@router.callback_query(F.data == 'activate')
async def process_activate(callback: CallbackQuery):
    await callback.answer()
    kb = await build_main_keyboard()

    msg_text = "Добро пожаловать в главное меню 🖐"
    if isinstance(main_menu, dict):
        lang_data = main_menu.get('ru', main_menu)
        if isinstance(lang_data, dict):
            msg_text = lang_data.get('msg', msg_text)

    await callback.message.answer(
        text=msg_text,
        reply_markup=kb
    )

# Нажатие кнопки "Получить сигнал" / "Сигналы"
@router.callback_query(F.data.in_({'signals', 'get_signal', 'signal'}))
async def process_signals(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    has_sub = await check_user_sub(user_id)

    if has_sub:
        kb = signals_key()
        await callback.message.answer("📊 Выберите интересующую пару для получения сигнала:", reply_markup=kb)
    else:
        kb = await build_subscr_keyboard()
        msg_txt = "🔒 У вас нет активной подписки.\n\nОформите подписку, чтобы получить доступ к торговым сигналам!"
        if isinstance(subscribe, dict):
            lang_data = subscribe.get('ru', subscribe)
            if isinstance(lang_data, dict):
                msg_txt = lang_data.get('msg', msg_txt)
        await callback.message.answer(text=msg_txt, reply_markup=kb)

# Выдача сигнала по выбранной криптовалютной паре
@router.callback_query(F.data.in_({
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'PEPEUSDT', 'WIFUSDT', 'APTUSDT', 
    'XRPUSDT', 'SHIBUSDT', 'DOGEUSDT', 'BONKUSDT', 'TIAUSDT', 'BNBUSDT', 
    'SEIUSDT', 'WLDUSDT', 'ORDIUSDT', 'AVAXUSDT', 'NEARUSDT', 'ADAUSDT', 
    'DOTUSDT', 'UNFIUSDT', 'ATOMUSDT', 'XLMUSDT', 'ZECUSDT', 'LUNCUSDT', 
    'TONUSDT', 'LINKUSDT', 'LTCUSDT', 'DIAUSDT', 'TRUMPUSDT', 'VETUSDT', 
    'ALGOUSDT', 'ARBUSDT', 'EOSUSDT'
}))
async def process_pair_signal(callback: CallbackQuery):
    await callback.answer()
    
    user_id = callback.from_user.id
    if not await check_user_sub(user_id):
        kb = await build_subscr_keyboard()
        await callback.message.answer("🔒 Для получения сигналов нужна активная подписка.", reply_markup=kb)
        return

    pair_name = callback.data
    
    # Шаблон генерируемого сигнала
    signal_text = (
        f"📊 <b>Торговый сигнал: #{pair_name}</b>\n\n"
        f"<b>Тип сделки:</b> LONG 🟢\n"
        f"<b>Вход:</b> По рынку (Market)\n"
        f"<b>Плечо:</b> Cross 10x - 20x\n\n"
        f"🎯 <b>Цели:</b>\n"
        f"1. Take-Profit 1 📈\n"
        f"2. Take-Profit 2 🚀\n"
        f"3. Take-Profit 3 💎\n\n"
        f"🛑 <b>Stop-Loss:</b> По рискам (15%)"
    )
    
    kb = back_fter_pay_key()
    await callback.message.answer(text=signal_text, reply_markup=kb)

# Нажатие кнопки "Подписка" / "Профиль" / "Тарифы"
@router.callback_query(F.data.in_({'sub', 'subscribe', 'profile', 'tarifs'}))
async def process_subscription(callback: CallbackQuery):
    await callback.answer()
    kb = await build_tarifs_keyboard()
    
    msg_txt = "💳 Выберите подходящий тариф подписки:"
    if isinstance(tarifs, dict):
        lang_data = tarifs.get('ru', tarifs)
        if isinstance(lang_data, dict):
            msg_txt = lang_data.get('msg', msg_txt)

    await callback.message.answer(text=msg_txt, reply_markup=kb)

# Кнопка возврата в главное меню
@router.callback_query(F.data == 'back_main')
async def process_back_main(callback: CallbackQuery):
    await callback.answer()
    kb = await build_main_keyboard()
    
    msg_text = "Главное меню:"
    if isinstance(main_menu, dict):
        lang_data = main_menu.get('ru', main_menu)
        if isinstance(lang_data, dict):
            msg_text = lang_data.get('msg', msg_text)

    await callback.message.answer(
        text=msg_text,
        reply_markup=kb
    )

# --- Точка входа ---
async def main():
    dp = Dispatcher(storage=storage)
    dp.message.middleware(BlacklistMiddleware(db_path='database.db'))
    dp.callback_query.middleware(BlacklistMiddleware(db_path='database.db'))

    dp.include_router(router)
    dp.include_router(admin_router)
    dp.include_router(pay_router)

    await init_db()

    app = web.Application()
    app.router.add_post(WEBHOOK_PATH_CRYPTOBOT, handle_postback)
    app.router.add_post(WEBHOOK_CIS_PAY, handle_postback)
    app.router.add_post(WEBHOOK_CRISTAL_PAY, handle_postback)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 3002))
    site = web.TCPSite(runner, '0.0.0.0', port)

    # Удаление вебхука для предотвращения TelegramConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info(f"Веб-сервер запущен на порту {port}. Запуск Polling...")

    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")
