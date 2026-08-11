#!/usr/bin/env python3
import os
import datetime
import json
import time
import logging
import contextlib
import asyncio
import random
import sqlite3
from typing import Any, Awaitable, Callable, Dict

import aiohttp
import aiosqlite
import numpy as np
import mplfinance as mpf
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot, Dispatcher, F, BaseMiddleware, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ChatJoinRequest, Message, CallbackQuery, TelegramObject, InputMediaPhoto, FSInputFile

import config
from db import execute_query
from creator_menu import router as admin_router, update_subscribe
from keyboards import (
    start_key, reg_key, deposit_key, main_keyboard, set_comands, subscr_key, StepsForm,
    tarifs_key, method_keys, signals_key, get_signal_key, profile_key, method_keys_menu,
    next_key, coonstruct_key, back_fter_pay_key
)
from languages import main_menu, activate_button, tarifs, subscribe, profile, signal_menu_mes
from payments import router as pay_router


# Динамическое подключение Redis из переменной окружения REDIS_URL
redis_url = os.getenv("REDIS_URL", "redis://redis.railway.internal:6379/0")
storage = RedisStorage.from_url(redis_url)

BOT_TOKEN = config.token

WEBHOOK_PATH_CRYPTOBOT = '/369546:AAxPmfahjiLrKIIgDNzwLtkhtlVjtIl1SPi'
WEBHOOK_CRISTAL_PAY = '/cristal_pay'
WEBHOOK_CIS_PAY = '/cis_pay'

bot: Bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 3002
router = Router()


def calculate_percentage_difference(current_price, new_price):
    difference = new_price - current_price
    percentage_difference = (difference / current_price) * 100
    return percentage_difference


class BlacklistMiddleware(BaseMiddleware):
    def __init__(self, db_path: str):
        self.db_path = db_path
        super().__init__()

    async def is_user_blacklisted(self, user_id: int) -> bool:
        query = 'SELECT * FROM black_list WHERE user_id = ?'
        params = (user_id,)
        result = await execute_query(query, params, False, 1)
        return result is not None

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id and await self.is_user_blacklisted(user_id):
            return  # Игнорируем событие от пользователя из черного списка

        return await handler(event, data)


async def updatge_sub_cryptobot(user_id, amount, bot: Bot):
    member = await bot.get_chat_member(int(user_id), int(user_id))
    lang = member.user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    now = datetime.datetime.now()
    str_time = now.strftime("%Y-%m-%d %H:%M:%S")

    query = 'SELECT date_start_sub, date_end_sub FROM users WHERE user_id = ?'
    params = (user_id,)
    date = await execute_query(query, params, False, 2)

    date_start_sub, date_end_sub = date[0] if date else (None, None)
    days_to_add = 0

    if int(amount) == 99:
        days_to_add = 30
        subscr = 'month'
    elif int(amount) == 499:
        days_to_add = 180
        subscr = 'six'
    elif int(amount) == 799:
        days_to_add = 365
        subscr = 'year'
    else:
        subscr = 'month'

    if date_end_sub:
        if date_end_sub > str_time:
            new_end_date = datetime.datetime.strptime(date_end_sub, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=days_to_add)
        else:
            new_end_date = now + datetime.timedelta(days=days_to_add)
    else:
        new_end_date = now + datetime.timedelta(days=days_to_add)

    update_query = 'UPDATE users SET date_end_sub = ?, sub_name = ? WHERE user_id = ?'
    params = (new_end_date.strftime("%Y-%m-%d %H:%M:%S"), subscr, user_id)
    await execute_query(update_query, params, True, 0)

    mes_query = 'SELECT mes_pay_id FROM users WHERE user_id = ?'
    params = (user_id,)
    mes_id = await execute_query(mes_query, params, False, 1)
    mes_id = mes_id[0]
    await bot.edit_message_reply_markup(chat_id=int(user_id), message_id=int(mes_id), reply_markup=None)

    if lang == 'ru':
        msg = (f'✅Счет успешно оплачен.'
               f'\n\n<b>🔔Вы успешно продлили подписку до {new_end_date.strftime("%Y-%m-%d %H:%M:%S")}</b>')
    else:
        msg = (f'✅The payment was successfully.'
               f'\n\n<b>🔔You have successfully extended your subscription until {new_end_date.strftime("%Y-%m-%d %H:%M:%S")}</b>')

    await bot.send_message(user_id, msg, reply_markup=back_fter_pay_key())

    member = await bot.get_chat_member(int(user_id), int(user_id))
    user_link = f"<a href='tg://user?id={member.user.id}'>{member.user.first_name or member.user.id}</a>"

    if int(amount) > 800:
        amount = round(int(amount) / 90, 1)

    await bot.send_message(chat_id=config.stats_id, text=f'💰Пользователь {user_link} совершил платеж на {amount}$')
    query = 'UPDATE creator SET all_sum_deposit = all_sum_deposit + ? WHERE user_id = ?'
    params = (float(amount), config.admin_id)
    await execute_query(query, params, True, 0)


async def handle_postback(request):
    if request.path == WEBHOOK_PATH_CRYPTOBOT:
        try:
            body = await request.text()
            data = json.loads(body)
            invoice = data.get('payload')
            amount = invoice.get('amount')
            invoice_id = invoice.get('invoice_id')
            query = 'SELECT user_id FROM users WHERE invoice_id = ?'
            params = (int(invoice_id),)
            user_id = await execute_query(query, params, False, 1)
            user_id = user_id[0]
            await updatge_sub_cryptobot(user_id, amount, bot)

            return web.Response(text="Webhook processed", status=200)
        except Exception as e:
            logging.error(f"Ошибка обработки вебхука: {str(e)}")

    if request.path == WEBHOOK_CIS_PAY:
        try:
            body = await request.text()
            data = json.loads(body)
            status = data.get('status')
            if status == 'success':
                amount = data.get('amount')
                tg_user_id = data.get('custom_fields')
                await updatge_sub_cryptobot(tg_user_id, amount, bot)

            return web.Response(text="Webhook processed", status=200)
        except Exception as e:
            logging.error(f"Ошибка обработки вебхука: {str(e)}")

    if request.path == WEBHOOK_CRISTAL_PAY:
        try:
            body = await request.text()
            data = json.loads(body)
            state = data.get('state')
            if state == 'payed':
                amount = data.get('initial_amount')
                tg_user_id = data.get('extra')
                await updatge_sub_cryptobot(tg_user_id, amount, bot)

            return web.Response(text="Webhook processed", status=200)
        except Exception as e:
            logging.error(f"Ошибка обработки вебхука: {str(e)}")


@router.message(F.text == '/start')
async def get_welcome(message: Message, bot: Bot):
    await set_comands(bot)
    now = datetime.datetime.now()
    str_time = now.strftime("%Y-%m-%d %H:%M:%S")
    user_id = message.from_user.id
    query = 'INSERT OR IGNORE INTO users (user_id,add_date) VALUES (?,?)'
    params = (user_id, str_time)
    await execute_query(query, params, commit=True, one=0)

    query = 'SELECT check_sub FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 1)
    is_sub = data[0]

    query = 'SELECT sub_name FROM users WHERE user_id = ?'
    params = (user_id,)
    data = await execute_query(query, params, False, 1)
    sub_name = data[0]

    lang = message.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    if is_sub == 0:
        if sub_name == '0':
            msg = activate_button.get(f'{lang}').get('msg')
            activate = activate_button.get(f'{lang}').get('name')
            photo_name = activate_button.get(f'{lang}').get('photo')
            photo = FSInputFile(path=fr'images/{photo_name}')
            await bot.send_photo(chat_id=user_id, photo=photo, caption=msg, reply_markup=start_key(activate))
        elif sub_name == '1':
            user_link = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
            msg = tarifs.get(f'{lang}').get('msg').format(user_link=user_link)
            free = tarifs.get(f'{lang}').get('free_24')
            month = tarifs.get(f'{lang}').get('month')
            six = tarifs.get(f'{lang}').get('six')
            year = tarifs.get(f'{lang}').get('year')
            fre_ref = tarifs.get(f'{lang}').get('free_ref')

            query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
            params = (config.admin_id,)
            data = await execute_query(query, params, False, 2)
            reviews, link_reviews, is_help, link_help, is_button_free = data[0]
            rew = main_menu.get(f'{lang}').get('rew')
            help = main_menu.get(f'{lang}').get('help')

            if lang == 'ru':
                msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
            else:
                msg = '💰<b>Choose a tariff, and start earning!</b>'

            await bot.send_message(user_id, text=msg, reply_markup=tarifs_key(
                free=free, month=month, six=six, year=year, fre_ref=fre_ref,
                is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
                is_help=is_help, help=help, url_help=link_help, is_btn_free=int(is_button_free)
            ))
        else:
            query = 'SELECT is_ref FROM users WHERE user_id = ?'
            params = (user_id,)
            data = await execute_query(query, params, False, 1)
            is_ref = data[0]

            msg = main_menu.get(f'{lang}').get('msg')
            signals = main_menu.get(f'{lang}').get('signals')
            profile = main_menu.get(f'{lang}').get('profile')
            free_get_bot = main_menu.get(f'{lang}').get('free_get_bot')
            rew = main_menu.get(f'{lang}').get('rew')
            help = main_menu.get(f'{lang}').get('help')

            query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
            params = (config.admin_id,)
            data = await execute_query(query, params, False, 2)
            reviews, link_reviews, is_help, link_help, is_button_free = data[0]

            await bot.send_message(user_id, msg, reply_markup=main_keyboard(
                signals=f'{signals}', profile=f'{profile}',
                is_free=int(is_ref), get_free=f'{free_get_bot}',
                is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
                is_help=is_help, help=help, url_help=link_help, is_btn_free=is_button_free
            ))

    elif is_sub == 1:
        query = 'SELECT channel_link,channel_id FROM creator WHERE user_id = ?'
        params = (config.admin_id,)
        data = await execute_query(query, params, False, 2)
        link, channel_id = data[0]

        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            if sub_name == '0':
                msg = activate_button.get(f'{lang}').get('msg')
                activate = activate_button.get(f'{lang}').get('name')
                photo_name = activate_button.get(f'{lang}').get('photo')
                photo = FSInputFile(path=fr'images/{photo_name}')
                await bot.send_photo(chat_id=user_id, photo=photo, caption=msg, reply_markup=start_key(activate))
            elif sub_name == '1':
                user_link = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
                msg = tarifs.get(f'{lang}').get('msg').format(user_link=user_link)
                free = tarifs.get(f'{lang}').get('free_24')
                month = tarifs.get(f'{lang}').get('month')
                six = tarifs.get(f'{lang}').get('six')
                year = tarifs.get(f'{lang}').get('year')
                fre_ref = tarifs.get(f'{lang}').get('free_ref')

                query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
                params = (config.admin_id,)
                data = await execute_query(query, params, False, 2)
                reviews, link_reviews, is_help, link_help, is_button_free = data[0]
                rew = main_menu.get(f'{lang}').get('rew')
                help = main_menu.get(f'{lang}').get('help')

                if lang == 'ru':
                    msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
                else:
                    msg = '💰<b>Choose a tariff, and start earning!</b>'

                await bot.send_message(user_id, text=msg, reply_markup=tarifs_key(
                    free=free, month=month, six=six, year=year, fre_ref=fre_ref,
                    is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
                    is_help=is_help, help=help, url_help=link_help, is_btn_free=int(is_button_free)
                ))
            else:
                query = 'SELECT is_ref FROM users WHERE user_id = ?'
                params = (user_id,)
                data = await execute_query(query, params, False, 1)
                is_ref = data[0]

                msg = main_menu.get(f'{lang}').get('msg')
                signals = main_menu.get(f'{lang}').get('signals')
                profile = main_menu.get(f'{lang}').get('profile')
                free_get_bot = main_menu.get(f'{lang}').get('free_get_bot')
                rew = main_menu.get(f'{lang}').get('rew')
                help = main_menu.get(f'{lang}').get('help')

                query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
                params = (config.admin_id,)
                data = await execute_query(query, params, False, 2)
                reviews, link_reviews, is_help, link_help, is_button_free = data[0]

                await bot.send_message(user_id, msg, reply_markup=main_keyboard(
                    signals=f'{signals}', profile=f'{profile}',
                    is_free=int(is_ref), get_free=f'{free_get_bot}',
                    is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
                    is_help=is_help, help=help, url_help=link_help, is_btn_free=is_button_free
                ))
        else:
            msg = subscribe.get(f'{lang}').get('msg')
            bnt1 = subscribe.get(f'{lang}').get('btn1')
            btn2 = subscribe.get(f'{lang}').get('bnt2')
            await bot.send_message(user_id, msg, reply_markup=subscr_key(link, bnt1, btn2))


@router.callback_query(F.data == 'chek_sub')
async def check_subscribe(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    query = 'SELECT channel_id FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 1)
    channel_id = data[0]

    member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
    query = 'SELECT sub_name FROM users WHERE user_id = ?'
    params = (user_id,)
    data = await execute_query(query, params, False, 1)
    sub_name = int(data[0])

    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    if member.status in ['member', 'administrator', 'creator']:
        await bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        if sub_name == 0:
            msg = activate_button.get(f'{lang}').get('msg')
            activate = activate_button.get(f'{lang}').get('name')
            photo_name = activate_button.get(f'{lang}').get('photo')
            photo = FSInputFile(path=fr'images/{photo_name}')
            await bot.send_photo(chat_id=user_id, photo=photo, caption=msg, reply_markup=start_key(activate))
        elif sub_name == 1:
            user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
            msg = tarifs.get(f'{lang}').get('msg').format(user_link=user_link)
            free = tarifs.get(f'{lang}').get('free_24')
            month = tarifs.get(f'{lang}').get('month')
            six = tarifs.get(f'{lang}').get('six')
            year = tarifs.get(f'{lang}').get('year')
            fre_ref = tarifs.get(f'{lang}').get('free_ref')

            query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
            params = (config.admin_id,)
            data = await execute_query(query, params, False, 2)
            reviews, link_reviews, is_help, link_help, is_button_free = data[0]
            rew = main_menu.get(f'{lang}').get('rew')
            help = main_menu.get(f'{lang}').get('help')

            if lang == 'ru':
                msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
            else:
                msg = '💰<b>Choose a tariff, and start earning!</b>'

            await bot.send_message(user_id, text=msg, reply_markup=tarifs_key(
                free=free, month=month, six=six, year=year, fre_ref=fre_ref,
                is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
                is_help=is_help, help=help, url_help=link_help, is_btn_free=int(is_button_free)
            ))
        else:
            query = 'SELECT is_ref FROM users WHERE user_id = ?'
            params = (user_id,)
            data = await execute_query(query, params, False, 1)
            is_ref = data[0]

            msg = main_menu.get(f'{lang}').get('msg')
            signals = main_menu.get(f'{lang}').get('signals')
            profile = main_menu.get(f'{lang}').get('profile')
            free_get_bot = main_menu.get(f'{lang}').get('free_get_bot')
            rew = main_menu.get(f'{lang}').get('rew')
            help = main_menu.get(f'{lang}').get('help')

            query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
            params = (config.admin_id,)
            data = await execute_query(query, params, False, 2)
            reviews, link_reviews, is_help, link_help, is_button_free = data[0]

            await bot.send_message(user_id, msg, reply_markup=main_keyboard(
                signals=f'{signals}', profile=f'{profile}',
                is_free=int(is_ref), get_free=f'{free_get_bot}',
                is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
                is_help=is_help, help=help, url_help=link_help, is_btn_free=is_button_free
            ))
    else:
        if lang == 'ru':
            msg = '🔴Вы не подписались на канал🔴'
        else:
            msg = "🔴You haven't subscribed to the channel🔴"

        await call.answer(f'{msg}', show_alert=True)


@router.callback_query(F.data == 'activate')
async def get_activate(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id

    await bot.delete_message(user_id, call.message.message_id)
    user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"

    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    msg = tarifs.get(f'{lang}').get('msg').format(user_link=user_link)

    if lang == 'ru':
        btn_name = 'Продолжить'
    else:
        btn_name = 'Next'

    await bot.send_message(user_id, msg, reply_markup=next_key(btn_name))


@router.callback_query(F.data == 'activate_second')
async def second_active_message(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    query = 'UPDATE users SET sub_name = 1 WHERE user_id = ?'
    params = (user_id,)
    await execute_query(query, params, True, 0)

    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    free = tarifs.get(f'{lang}').get('free_24')
    month = tarifs.get(f'{lang}').get('month')
    six = tarifs.get(f'{lang}').get('six')
    year = tarifs.get(f'{lang}').get('year')
    fre_ref = tarifs.get(f'{lang}').get('free_ref')

    query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    reviews, link_reviews, is_help, link_help, is_button_free = data[0]
    rew = main_menu.get(f'{lang}').get('rew')
    help = main_menu.get(f'{lang}').get('help')

    if lang == 'ru':
        msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
    else:
        msg = '💰<b>Choose a tariff, and start earning!</b>'

    await bot.delete_message(user_id, call.message.message_id)
    await bot.send_message(user_id, msg, reply_markup=tarifs_key(
        free=free, month=month, six=six, year=year, fre_ref=fre_ref,
        is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
        is_help=is_help, help=help, url_help=link_help, is_btn_free=int(is_button_free)
    ))


async def timer_day(bot: Bot, user_id: int, lang: str):
    await asyncio.sleep(86400)
    query = 'UPDATE users SET date_start_sub = ?,date_end_sub = ?, sub_name = ? WHERE user_id = ?'
    params = ('0', '0', 2, user_id)
    await execute_query(query, params, True, 0)

    if lang == 'ru':
        msg = '🔔<b>Ваша пробная подписка завершена!</b>\n🔥Вы можете приобрести подписку в главном меню или получить доступ в бота бесплатно.'
    else:
        msg = '🔔 </b>Your trial subscription has ended!</b>\n🔥 You can purchase a subscription in the main menu or get free bot access.'

    await bot.send_message(chat_id=user_id, text=msg)


@router.callback_query(F.data == 'get_bot_free_day')
async def open_trial_version(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    query = 'SELECT is_free_get FROM users WHERE user_id = ?'
    params = (user_id,)
    data = await execute_query(query, params, False, 1)
    is_free_get = data[0]

    if int(is_free_get) == 0:
        if lang == 'ru':
            msg = '✅Вам успешно предоставлен доступ на 24 часа'
        else:
            msg = '✅ Success! Your 24-hour access is now active!'

        await call.answer(msg, show_alert=True)
        # open_menu_signals implementation should be called here
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        future_time = (now + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        query = 'UPDATE users SET date_start_sub = ?,date_end_sub = ?, sub_name = ?,is_free_get = 1 WHERE user_id = ?'
        params = (current_time, future_time, 'day', user_id)
        await execute_query(query, params, True, 0)
        asyncio.create_task(timer_day(bot, user_id, lang))
    else:
        if lang == 'ru':
            msg = '⚠️Вы уже активировали пробный период!'
        else:
            msg = '⚠️ You have already activated the trial period!'

        await call.answer(msg, show_alert=True)


@router.callback_query(F.data.in_(['month_99', 'six_499', 'year_799']))
async def open_buy_subcsr(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)

    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    summ = str(call.data).split('_')[1]

    if lang == 'ru':
        msg = f'💰<b>Сумма:</b> <code>{summ}$</code>\nВыберите способ оплаты⬇️'
    else:
        msg = f'💰<b>Amount:</b> <code>{summ}$</code>\nSelect payment method⬇️'

    query = 'SELECT crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    crypto_bot, smart_glocal, crystal_pay, ammer_pay, cis_pay = data[0]

    await bot.send_message(user_id, msg, reply_markup=method_keys(
        is_crystal=crystal_pay, is_bot=crypto_bot, is_cis=cis_pay,
        is_ammer=ammer_pay, is_smart=smart_glocal
    ))
    await state.update_data(summ_pay=int(summ))


@router.callback_query(F.data == 'profile')
async def open_subscr_menu(call: CallbackQuery, bot: Bot, state):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    query = 'SELECT date_end_sub FROM users WHERE user_id = ?'
    params = (user_id,)
    data = await execute_query(query, params, False, 1)
    date_end_sub = data[0]

    msg = profile.get(f'{lang}').get('msg').format(end_date=f'{date_end_sub}', user_id=user_id)
    month = tarifs.get(f'{lang}').get('month')
    six = tarifs.get(f'{lang}').get('six')
    year = tarifs.get(f'{lang}').get('year')

    await bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id,
                                reply_markup=profile_key(month, six, year))


@router.callback_query(F.data.in_(['paymonth_99', 'paysix_499', 'payyear_799']))
async def buy_subscr_main_menu(call: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)

    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    summ = str(call.data).split('_')[1]

    if lang == 'ru':
        msg = f'💰<b>Сумма:</b> <code>{summ}$</code>\nВыберите способ оплаты⬇️'
    else:
        msg = f'💰<b>Amount:</b> <code>{summ}$</code>\nSelect payment method⬇️'

    query = 'SELECT crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    crypto_bot, smart_glocal, crystal_pay, ammer_pay, cis_pay = data[0]

    await bot.send_message(user_id, msg, reply_markup=method_keys_menu(
        is_crystal=crystal_pay, is_bot=crypto_bot, is_cis=cis_pay,
        is_ammer=ammer_pay, is_smart=smart_glocal
    ))
    await state.update_data(summ_pay=summ)


@router.callback_query(F.data == 'back_active')
async def back_active_menu(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)

    lang = call.from_user.language_code
    if lang != 'ru' and lang != 'en':
        lang = 'en'

    user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"
    msg = tarifs.get(f'{lang}').get('msg').format(user_link=user_link)
    free = tarifs.get(f'{lang}').get('free_24')
    month = tarifs.get(f'{lang}').get('month')
    six = tarifs.get(f'{lang}').get('six')
    year = tarifs.get(f'{lang}').get('year')
    fre_ref = tarifs.get(f'{lang}').get('free_ref')

    query = 'SELECT reviews,link_reviews,help,link_help, is_button_free FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    reviews, link_reviews, is_help, link_help, is_button_free = data[0]
    rew = main_menu.get(f'{lang}').get('rew')
    help = main_menu.get(f'{lang}').get('help')

    if lang == 'ru':
        msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
    else:
        msg = '💰<b>Choose a tariff, and start earning!</b>'

    await bot.send_message(user_id, text=msg, reply_markup=tarifs_key(
        free=free, month=month, six=six, year=year, fre_ref=fre_ref,
        is_rewievs=reviews, reviews=rew, url_reviews=link_reviews,
        is_help=is_help, help=help, url_help=link_help, is_btn_free=int(is_button_free)
    ))


@router.callback_query(F.data == 'check_register')
async def check_register(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    query = 'SELECT platform_id FROM users WHERE user_id = ?'
    params = (user_id,)
    is_reg = await execute_query(query, params, False, 1)
    is_reg = is_reg[0]

    if is_reg != 0:
        query = 'UPDATE users SET try_numbers = 0 WHERE user_id = ?'
        params = (user_id,)
        await execute_query(query, params, True, 0)

        await bot.delete_message(user_id, call.message.message_id)
        msg = (f'<b>Ты правильно зарегистрировал аккаунт и уже находишься у нас в базе 💎</b>'
               f'\n\n<b>Теперь пополни свой торговый счёт на сумму от 5О.ОО$</b>'
               f'\n\n<i>⛔️ Если ты не совершил пополнение баланса, не нажимай на кнопку "счёт пополнил", алгоритм тебя просто заблокирует за обман❌</i>'
               f'\n\nЕсли ты уже пополнил свой аккаунт на сумму от 5О.ОО$ нажимай на кнопку "Cчёт пополнил" и получай мгновенный доступ'
               f'\n\nСперва пополни свой аккаунт, а уже после нажимай на кнопку ниже 🙏')
        photo = FSInputFile(path='images/dep.jpg')
        await bot.send_photo(user_id, photo, caption=msg, reply_markup=deposit_key())
    else:
        query = 'SELECT user_id FROM creator'
        data = await execute_query(query, (), False, 2)
        admin_list = [item for sublist in data for item in sublist]

        query = 'UPDATE users SET try_numbers = try_numbers + 1 WHERE user_id = ?'
        params = (user_id,)
        await execute_query(query, params, True, 0)

        query = 'SELECT try_numbers FROM users WHERE user_id = ?'
        params = (user_id,)
        data = await execute_query(query, params, False, 1)
        try_numbers = data[0]

        if try_numbers < 3:
            await call.answer(f'❌Регистрация не найдена❌\nНеудачных попыток {try_numbers}/3', show_alert=True)
        elif try_numbers == 3:
            if call.from_user.id in admin_list:
                await call.answer('Вы являетесь администратором! Вам предоставлен доступ!', show_alert=True)
                query = 'UPDATE users SET platform_id = 12345678 WHERE user_id = ?'
                params = (user_id,)
                await execute_query(query, params, True, 0)
            else:
                query = 'INSERT OR IGNORE INTO black_list (user_id) VALUES (?)'
                params = (user_id,)
                await execute_query(query, params, commit=True, one=0)
                await call.answer(f'❌Регистрация не найдена❌\nВы заблокированы', show_alert=True)
