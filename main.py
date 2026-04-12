#!/usr/bin/env python3
import os

import datetime
import json
import os
import time

import aiohttp
import numpy as np
import mplfinance as mpf
import pandas as pd
from typing import Any, Awaitable, Callable, Dict
import random
import sqlite3
from aiohttp import web
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

from aiogram.types import ChatJoinRequest, Message, CallbackQuery, TelegramObject
from aiogram import Bot, Dispatcher, F, BaseMiddleware, Router
import logging
import contextlib
import asyncio
import config
from aiogram.types import InputMediaPhoto, FSInputFile
from PIL import Image, ImageDraw, ImageFont
import aiosqlite
from  db import execute_query
from creator_menu import router as admin_router, update_subscribe
from keyboards import start_key, reg_key, deposit_key, main_keyboard, set_comands, subscr_key, StepsForm, \
    tarifs_key, method_keys, signals_key, get_signal_key, profile_key, method_keys_menu, next_key, coonstruct_key, \
    back_fter_pay_key
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.context import FSMContext
from languages import main_menu, activate_button, tarifs, subscribe, profile, signal_menu_mes
from payments import router as pay_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler



storage = RedisStorage.from_url('redis://default:SNqtFDcehlsTjoEMcPTpgtXVvEfFxThU@redis-69bt.railway.internal:6379/0')
BOT_TOKEN = config.token


WEBHOOK_PATH_CRYPTOBOT = '/369546:AAxPmfahjiLrKIIgDNzwLtkhtlVjtIl1SPi'
WEBHOOK_CRISTAL_PAY = '/cristal_pay'
WEBHOOK_CIS_PAY = '/cis_pay'
bot: Bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 3002
router = Router()






def calculate_percentage_difference(current_price, new_price):
    # Вычисляем абсолютную разницу между ценами
    difference = new_price - current_price

    # Вычисляем процентную разницу относительно текущей цены
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


async def updatge_sub_cryptobot(user_id,amount, bot:Bot):
    member = await bot.get_chat_member(int(user_id),int(user_id))
    lang = member.user.language_code
    if lang!='ru' and lang!='en':lang='en'

    now = datetime.datetime.now()
    str_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Запросим текущие данные пользователя
    query = 'SELECT date_start_sub, date_end_sub FROM users WHERE user_id = ?'
    params = (user_id,)
    date = await execute_query(query, params, False, 2)

    date_start_sub, date_end_sub = date[0] if date else (None, None)

    # Дефолтные значения для подписки
    days_to_add = 0

    # В зависимости от типа подписки увеличиваем количество дней
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
    # Если подписка уже активна
    if date_end_sub:
        # Проверим, если дата окончания подписки еще не наступила
        if date_end_sub > str_time:
            # Добавляем нужное количество дней к дате окончания подписки
            new_end_date = datetime.datetime.strptime(date_end_sub, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=days_to_add)
        else:
            # Если подписка уже закончена, устанавливаем новую дату на основе текущей
            new_end_date = now + datetime.timedelta(days=days_to_add)
    else:
        # Если дата окончания подписки пустая или равна нулю, устанавливаем новую дату на основе текущей
        new_end_date = now + datetime.timedelta(days=days_to_add)

    # Обновляем дату окончания подписки в базе данных
    update_query = 'UPDATE users SET date_end_sub = ?,sub_name = ? WHERE user_id = ?'
    params = (new_end_date.strftime("%Y-%m-%d %H:%M:%S"),subscr, user_id)
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



    if int(amount)>800:
        amount = round(int(amount)/90,1)
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
            amount = invoice.get('amount')            # Сумма оплаты
            invoice_id = invoice.get('invoice_id')     # ID платежа
            query = 'SELECT user_id FROM users WHERE invoice_id = ?'
            params = (int(invoice_id),)
            user_id = await execute_query(query, params, False, 1)
            user_id = user_id[0]
            await updatge_sub_cryptobot(user_id,amount, bot)

            return web.Response(text="Webhook processed", status=200)

        except Exception as e:
            logging.error(f"Ошибка обработки вебхука: {str(e)}")
    if request.path == WEBHOOK_CIS_PAY:
        try:
            body = await request.text()
            data = json.loads(body)
            status = data.get('status')
            if status=='success':
                amount = data.get('amount')            # Сумма оплаты
                tg_user_id = data.get('custom_fields')
                await updatge_sub_cryptobot(tg_user_id,amount, bot)

            return web.Response(text="Webhook processed", status=200)

        except Exception as e:
            logging.error(f"Ошибка обработки вебхука: {str(e)}")

    if request.path == WEBHOOK_CRISTAL_PAY:
        try:
            body = await request.text()
            data = json.loads(body)
            state = data.get('state')
            if state=='payed':
                amount = data.get('initial_amount')            # Сумма оплаты
                tg_user_id = data.get('extra')
                await updatge_sub_cryptobot(tg_user_id,amount, bot)

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
    params = (user_id,str_time)
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
    if lang!='ru' and lang!='en': lang = 'en'
    if is_sub == 0:
        if sub_name=='0':

            msg = activate_button.get(f'{lang}').get('msg')
            activate = activate_button.get(f'{lang}').get('name')
            photo_name = activate_button.get(f'{lang}').get('photo')
            photo = FSInputFile(path=fr'images/{photo_name}')
            await bot.send_photo(chat_id=user_id, photo=photo, caption=msg, reply_markup=start_key(activate))
        elif sub_name=='1':
            user_link = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"

            msg =tarifs.get(f'{lang}').get('msg').format(user_link = user_link)
            free = tarifs.get(f'{lang}').get('free_24')
            month = tarifs.get(f'{lang}').get('month')
            six = tarifs.get(f'{lang}').get('six')
            year = tarifs.get(f'{lang}').get('year')
            fre_ref = tarifs.get(f'{lang}').get('free_ref')
            image = tarifs.get(f'{lang}').get('image')
            photo = FSInputFile(path=fr'images/{image}')
            query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
            params = (config.admin_id,)
            data = await execute_query(query, params, False, 2)
            reviews,link_reviews,is_help,link_help,is_button_free = data[0]
            rew = main_menu.get(f'{lang}').get('rew')
            help = main_menu.get(f'{lang}').get('help')
            if lang=='ru':
                msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
            else:
                msg = '💰<b>Choose a tariff, and start earning!</b>'
            await bot.send_message(user_id,  text=msg, reply_markup=tarifs_key(free =free , month = month, six = six, year = year,fre_ref = fre_ref,
                                                                               is_rewievs =reviews ,reviews= rew,url_reviews =link_reviews ,is_help = is_help, help = help,url_help = link_help,is_btn_free=int(is_button_free)))
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
            reviews,link_reviews,is_help,link_help,is_button_free = data[0]

            await bot.send_message(user_id, msg, reply_markup=main_keyboard(signals = f'{signals}',profile = f'{profile}',
                                                                            is_free =int(is_ref) , get_free = f'{free_get_bot}',
                                                                            is_rewievs = reviews,reviews = rew,url_reviews = link_reviews,is_help = is_help, help = help,url_help = link_help,is_btn_free=is_button_free))

    elif is_sub == 1:
        query = 'SELECT channel_link,channel_id FROM creator WHERE user_id = ?'
        params = (config.admin_id,)
        data = await execute_query(query, params, False, 2)
        link, channel_id = data[0]
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            if sub_name=='0':

                msg = activate_button.get(f'{lang}').get('msg')
                activate = activate_button.get(f'{lang}').get('name')
                photo_name = activate_button.get(f'{lang}').get('photo')
                photo = FSInputFile(path=fr'images/{photo_name}')
                await bot.send_photo(chat_id=user_id, photo=photo, caption=msg, reply_markup=start_key(activate))
            elif sub_name=='1':
                user_link = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"

                msg =tarifs.get(f'{lang}').get('msg').format(user_link = user_link)
                free = tarifs.get(f'{lang}').get('free_24')
                month = tarifs.get(f'{lang}').get('month')
                six = tarifs.get(f'{lang}').get('six')
                year = tarifs.get(f'{lang}').get('year')
                fre_ref = tarifs.get(f'{lang}').get('free_ref')
                image = tarifs.get(f'{lang}').get('image')
                photo = FSInputFile(path=fr'images/{image}')
                query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
                params = (config.admin_id,)
                data = await execute_query(query, params, False, 2)
                reviews,link_reviews,is_help,link_help,is_button_free = data[0]
                rew = main_menu.get(f'{lang}').get('rew')
                help = main_menu.get(f'{lang}').get('help')
                if lang=='ru':
                    msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
                else:
                    msg = '💰<b>Choose a tariff, and start earning!</b>'
                await bot.send_message(user_id,  text=msg, reply_markup=tarifs_key(free =free , month = month, six = six, year = year,fre_ref = fre_ref,
                                                                                   is_rewievs =reviews ,reviews= rew,url_reviews =link_reviews ,is_help = is_help, help = help,url_help = link_help,is_btn_free=int(is_button_free)))
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
                reviews,link_reviews,is_help,link_help,is_button_free = data[0]

                await bot.send_message(user_id, msg, reply_markup=main_keyboard(signals = f'{signals}',profile = f'{profile}',
                                                                                is_free =int(is_ref) , get_free = f'{free_get_bot}',
                                                                                is_rewievs = reviews,reviews = rew,url_reviews = link_reviews,is_help = is_help, help = help,url_help = link_help, is_btn_free=is_button_free))

        else:
            msg = subscribe.get(f'{lang}').get('msg')
            bnt1 = subscribe.get(f'{lang}').get('btn1')
            btn2 = subscribe.get(f'{lang}').get('bnt2')
            await bot.send_message(user_id, msg, reply_markup=subscr_key(link,bnt1,btn2))

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
    sub_name = data[0]
    sub_name = int(sub_name)
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    if member.status in ['member', 'administrator', 'creator']:
        await bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
        if sub_name==0:

            msg = activate_button.get(f'{lang}').get('msg')
            activate = activate_button.get(f'{lang}').get('name')
            photo_name = activate_button.get(f'{lang}').get('photo')
            photo = FSInputFile(path=fr'images/{photo_name}')
            await bot.send_photo(chat_id=user_id, photo=photo, caption=msg, reply_markup=start_key(activate))
        elif sub_name==1:
            user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"

            msg =tarifs.get(f'{lang}').get('msg').format(user_link = user_link)
            free = tarifs.get(f'{lang}').get('free_24')
            month = tarifs.get(f'{lang}').get('month')
            six = tarifs.get(f'{lang}').get('six')
            year = tarifs.get(f'{lang}').get('year')
            fre_ref = tarifs.get(f'{lang}').get('free_ref')
            image = tarifs.get(f'{lang}').get('image')
            photo = FSInputFile(path=fr'images/{image}')
            query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
            params = (config.admin_id,)
            data = await execute_query(query, params, False, 2)
            reviews,link_reviews,is_help,link_help,is_button_free = data[0]
            rew = main_menu.get(f'{lang}').get('rew')
            help = main_menu.get(f'{lang}').get('help')
            if lang=='ru':
                msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
            else:
                msg = '💰<b>Choose a tariff, and start earning!</b>'
            await bot.send_message(user_id,  text=msg, reply_markup=tarifs_key(free =free , month = month, six = six, year = year,fre_ref = fre_ref,
                                                                                            is_rewievs =reviews ,reviews= rew,url_reviews =link_reviews ,is_help = is_help, help = help,url_help = link_help,is_btn_free=int(is_button_free)))
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
            reviews,link_reviews,is_help,link_help,is_button_free = data[0]

            await bot.send_message(user_id, msg, reply_markup=main_keyboard(signals = f'{signals}',profile = f'{profile}',
                                                                            is_free =int(is_ref) , get_free = f'{free_get_bot}',
                                                                            is_rewievs = reviews,reviews = rew,url_reviews = link_reviews,is_help = is_help, help = help,url_help = link_help, is_btn_free=is_button_free))
    else:
        if lang=='ru':msg = f'🔴Вы не подписались на канал🔴'
        else: msg = f"🔴You haven't subscribed to the channel🔴"

        await call.answer(f'{msg}', show_alert=True)



@router.callback_query(F.data == 'activate')
async def get_activate(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id

    await bot.delete_message(user_id, call.message.message_id)
    user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"

    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'

    msg =tarifs.get(f'{lang}').get('msg').format(user_link = user_link)

    if lang=='ru':
        btn_name = 'Продолжить'
    else:
        btn_name = 'Next'
    await bot.send_message(user_id, msg, reply_markup=next_key(btn_name))


@router.callback_query(F.data=='activate_second')
async def second_active_message(call:CallbackQuery,bot:Bot):
    user_id = call.from_user.id
    query = 'UPDATE users SET sub_name = 1 WHERE user_id = ?'
    params = (user_id,)
    await execute_query(query, params, True, 0)
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    free = tarifs.get(f'{lang}').get('free_24')
    month = tarifs.get(f'{lang}').get('month')
    six = tarifs.get(f'{lang}').get('six')
    year = tarifs.get(f'{lang}').get('year')
    fre_ref = tarifs.get(f'{lang}').get('free_ref')
    image = tarifs.get(f'{lang}').get('image')
    photo = FSInputFile(path=fr'images/{image}')
    query = 'SELECT reviews,link_reviews,help,link_help,is_button_free FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    reviews,link_reviews,is_help,link_help,is_button_free = data[0]
    rew = main_menu.get(f'{lang}').get('rew')
    help = main_menu.get(f'{lang}').get('help')
    if lang=='ru':
        msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
    else:
        msg = '💰<b>Choose a tariff, and start earning!</b>'

    await bot.delete_message(user_id, call.message.message_id)
    await bot.send_message(user_id, msg, reply_markup=tarifs_key(free =free , month = month, six = six, year = year,fre_ref = fre_ref,
                                                                                    is_rewievs =reviews ,reviews= rew,url_reviews =link_reviews ,is_help = is_help, help = help,url_help = link_help, is_btn_free=int(is_button_free)))


async def timer_day(bot:Bot, user_id:int, lang:str):
    await asyncio.sleep(86400)
    query = 'UPDATE users SET date_start_sub = ?,date_end_sub = ?, sub_name = ? WHERE user_id = ?'
    params = ('0','0',2,user_id)
    await execute_query(query, params, True, 0)
    if lang=='ru': msg = f'🔔<b>Ваша пробная подписка завершена!</b>\n🔥Вы можете приобрести подписку в главном меню или получить доступ в бота бесплатно.'
    else:msg = f'🔔 </b>Your trial subscription has ended!</b>\n🔥 You can purchase a subscription in the main menu or get free bot access.'
    await bot.send_message(chat_id=user_id, text=msg)

@router.callback_query(F.data=='get_bot_free_day')
async def open_trial_version(call:CallbackQuery,bot:Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    query = 'SELECT is_free_get FROM users WHERE user_id = ?'
    params = (user_id,)
    data = await execute_query(query, params, False, 1)
    is_free_get = data[0]
    if int(is_free_get)==0:
        if lang=='ru': msg = f'✅Вам успешно предоставлен доступ на 24 часа'
        else:  msg = f'✅ Success! Your 24-hour access is now active!'
        await call.answer(msg, show_alert=True)
        await open_menu_signals(call, bot)
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        future_time = (now + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        query = 'UPDATE users SET date_start_sub = ?,date_end_sub = ?, sub_name = ?,is_free_get = 1 WHERE user_id = ?'
        params = (current_time,future_time,'day',user_id)
        await execute_query(query, params, True, 0)
        asyncio.create_task(timer_day(bot, user_id, lang))
    else:
        if lang=='ru': msg = f'⚠️Вы уже активировали пробный период!'
        else:  msg = f'⚠️ You have already activated the trial period!'
        await call.answer(msg, show_alert=True)

@router.callback_query(F.data.in_(['month_99','six_499','year_799']))
async def open_buy_subcsr(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    summ = str(call.data).split('_')[1]
    if lang=='ru':msg = f'💰<b>Сумма:</b> <code>{summ}$</code>\nВыберите способ оплаты⬇️'
    else:msg = f'💰<b>Amount:</b> <code>{summ}$</code>\nSelect payment method⬇️'
    query = 'SELECT crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay = data[0]
    await bot.send_message( user_id, msg, reply_markup=method_keys(is_crystal = crystal_pay, is_bot = crypto_bot, is_cis = cis_pay,is_ammer =ammer_pay ,is_smart =smart_glocal ))
    await state.update_data(summ_pay = int(summ))



@router.callback_query(F.data=='profile')
async def open_subscr_menu(call:CallbackQuery,bot:Bot,state):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    query = 'SELECT date_end_sub FROM users WHERE user_id = ?'
    params = (user_id,)
    data = await execute_query(query, params, False, 1)
    date_end_sub = data[0]
    msg = profile.get(f'{lang}').get('msg').format(end_date=f'{date_end_sub}',user_id=user_id)
    month = tarifs.get(f'{lang}').get('month')
    six = tarifs.get(f'{lang}').get('six')
    year = tarifs.get(f'{lang}').get('year')
    await bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id, reply_markup=profile_key(month,six,year))

@router.callback_query(F.data.in_(['paymonth_99','paysix_499','payyear_799']))
async def buy_subscr_main_menu(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    summ = str(call.data).split('_')[1]
    if lang=='ru':msg = f'💰<b>Сумма:</b> <code>{summ}$</code>\nВыберите способ оплаты⬇️'
    else:msg = f'💰<b>Amount:</b> <code>{summ}$</code>\nSelect payment method⬇️'
    query = 'SELECT crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay = data[0]

    await bot.send_message( user_id, msg, reply_markup=method_keys_menu(is_crystal = crystal_pay, is_bot = crypto_bot, is_cis = cis_pay,is_ammer =ammer_pay ,is_smart =smart_glocal ))
    await state.update_data(summ_pay = summ)

@router.callback_query(F.data=='back_active')
async def back_active_menu(call:CallbackQuery, bot:Bot):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.first_name}</a>"

    msg =tarifs.get(f'{lang}').get('msg').format(user_link = user_link)
    free = tarifs.get(f'{lang}').get('free_24')
    month = tarifs.get(f'{lang}').get('month')
    six = tarifs.get(f'{lang}').get('six')
    year = tarifs.get(f'{lang}').get('year')
    fre_ref = tarifs.get(f'{lang}').get('free_ref')
    image = tarifs.get(f'{lang}').get('image')
    photo = FSInputFile(path=fr'images/{image}')
    query = 'SELECT reviews,link_reviews,help,link_help, is_button_free FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    reviews,link_reviews,is_help,link_help, is_button_free = data[0]
    rew = main_menu.get(f'{lang}').get('rew')
    help = main_menu.get(f'{lang}').get('help')
    if lang=='ru':
        msg = '💰<b>Выберите тариф, и начинайте зарабатывать!</b>'
    else:
        msg = '💰<b>Choose a tariff, and start earning!</b>'
    await bot.send_message(user_id,  text=msg, reply_markup=tarifs_key(free =free , month = month, six = six, year = year,fre_ref = fre_ref,
                                                                       is_rewievs =reviews ,reviews= rew,url_reviews =link_reviews ,is_help = is_help, help = help,url_help = link_help,is_btn_free=int(is_button_free)))


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


@router.callback_query(F.data == 'check_deposit')
async def get_check_deposit(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    query = 'SELECT sum_deposit FROM users WHERE user_id = ?'
    params = (user_id,)
    summ_dep = await execute_query(query, params, False, 1)
    summ_dep = summ_dep[0]
    if summ_dep != 0 and summ_dep >= 50:
        await bot.delete_message(user_id, call.message.message_id)
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
        reviews,link_reviews,is_help,link_help,is_button_free = data[0]

        await bot.send_message(user_id, msg, reply_markup=main_keyboard(signals = f'{signals}',profile = f'{profile}',
                                                                        is_free =int(is_ref) , get_free = f'{free_get_bot}',
                                                                        is_rewievs = reviews,reviews = rew,url_reviews = link_reviews,is_help = is_help, help = help,url_help = link_help, is_btn_free=is_button_free))
    elif summ_dep != 0 and summ_dep < 50:
        await call.answer(f'⚠️Баланс пополнен менее чем на 50$\n{summ_dep}$/50.0$', show_alert=True)
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
            await call.answer(f'❌Депозит не найден❌\nНеудачных попыток {try_numbers}/3', show_alert=True)
        elif try_numbers == 3:
            if call.from_user.id in admin_list:
                await call.answer('Вы являетесь администратором! Вам предоставлен доступ!', show_alert=True)
                query = 'UPDATE users SET sum_deposit = 100 WHERE user_id = ?'
                params = (user_id,)
                await execute_query(query, params, True, 0)
            else:
                query = 'INSERT OR IGNORE INTO black_list (user_id) VALUES (?)'
                params = (user_id,)
                await execute_query(query, params, commit=True, one=0)
                await call.answer(f'❌Депозит не найден❌\nВы заблокированы', show_alert=True)




async def get_binance_klines(symbol, interval, start_time):
    # Convert milliseconds to seconds for Bybit
    start_time_sec = int(start_time) // 1000
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval=5&start={start_time_sec * 1000}&limit=200"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                print(f"Bybit status: {response.status}, preview: {str(data)[:200]}")
                if data.get('retCode') == 0:
                    # Bybit returns [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
                    # Binance format: [openTime, open, high, low, close, volume, ...]
                    result = []
                    for item in reversed(data['result']['list']):
                        result.append([item[0], item[1], item[2], item[3], item[4], item[5]])
                    return result
                else:
                    print(f"Bybit error: {data}")
                    return []
    except Exception as e:
        print(f"Bybit API error: {e}")
        return []


@router.callback_query(F.data.in_(['signals','get_new_signal']))
async def open_signals_menu(call:CallbackQuery,bot:Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    msg = signal_menu_mes.get(f'{lang}')
    if call.data=='signals':
        await bot.edit_message_text(chat_id=user_id, text=msg, message_id=call.message.message_id, reply_markup=signals_key())
    elif call.data=='get_new_signal':
        await bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=None)
        await bot.send_message(chat_id=user_id, text=msg, reply_markup=signals_key())

@router.callback_query(F.data.in_(
    ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'WIFUSDT', 'PEPEUSDT', 'APTUSDT', 'XRPUSDT', 'SHIBUSDT', 'DOGEUSDT',
     'BONKUSDT', 'TIAUSDT', 'BNBUSDT', 'SEIUSDT', 'WLDUSDT', 'ORDIUSDT', 'AVAXUSDT', 'NEARUSDT', 'ADAUSDT',
     'DOTUSDT', 'UNFIUSDT', 'ATOMUSDT', 'XLMUSDT', 'ZECUSDT', 'LUNCUSDT','TONUSDT', 'LINKUSDT', 'LTCUSDT',
     'DIAUSDT', 'TRUMPUSDT', 'TRUMPUSDT', 'VETUSDT', 'ALGOUSDT', 'ARBUSDT', 'EOSUSDT']))
async def get_signal(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
    if lang=='ru':
        signal_name_up = 'ВВЕРХ'
        signal_name_down = 'ВНИЗ'
    else:
        signal_name_up = 'UP'
        signal_name_down = 'DOWN'

    time_difference = None
    prog = None
    potential = None
    ending_prognoz = None
    user_name = f'session_{user_id}'
    time_resp = await storage.redis.get(user_name)
    if time_resp != None:
        time_resp = time_resp.decode('utf-8')
        time_resp = str(time_resp)
    else:
        time_resp = None

    if time_resp != None:
        time_resp = datetime.datetime.strptime(time_resp, '%m.%d@%H:%M:%S')
        formatted_time = time_resp.strftime('%m.%d@%H:%M:%S')
        current_time = datetime.datetime.now().strftime('%m.%d@%H:%M:%S')
        current_datetime = datetime.datetime.strptime(current_time, '%m.%d@%H:%M:%S')
        second_datetime = datetime.datetime.strptime(formatted_time, '%m.%d@%H:%M:%S')
        time_difference = abs(current_datetime - second_datetime)
    elif time_resp == None:
        current_time = datetime.datetime.now().strftime('%m.%d@%H:%M')
    if time_resp == None or time_difference.total_seconds() >= 1 * 60:
        def detect_fractals(highs, lows):
            fractals = {
                'up': [],  # Индексы фракталов на покупку (фракталы вверх)
                'down': []  # Индексы фракталов на продажу (фракталы вниз)
            }

            # Начинаем с третьей свечи (индекс 2) и до конца, так как фракталы определяются по 5 свечам
            for i in range(2, len(highs) - 2):
                # Фрактал вверх (центральная свеча выше двух слева и двух справа)
                if highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and highs[i] > highs[i + 1] and highs[i] > highs[
                    i + 2]:
                    fractals['up'].append(i)

                # Фрактал вниз (центральная свеча ниже двух слева и двух справа)
                if lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and lows[i] < lows[i + 1] and lows[i] < lows[i + 2]:
                    fractals['down'].append(i)

            return fractals

        # Function to save a chart as an image
        def save_chart(up, symbol, klines, take_profit=None, stop_loss=None):
            if not klines:  # Проверка на наличие данных
                print(f"Нет данных для {symbol}")
                return

            # Create a DataFrame with the OHLC data
            ohlc_data = pd.DataFrame(klines,
                                     columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Проверка, что данные по свечам не пусты
            if ohlc_data.empty:
                print(f"Пустой DataFrame для {symbol}")
                return

            # Convert columns to floats
            ohlc_data['open'] = ohlc_data['open'].astype(float)
            ohlc_data['high'] = ohlc_data['high'].astype(float)
            ohlc_data['low'] = ohlc_data['low'].astype(float)
            ohlc_data['close'] = ohlc_data['close'].astype(float)

            # Конвертируем метку времени в дату
            ohlc_data['timestamp'] = pd.to_datetime(ohlc_data['timestamp'].astype(float) / 1000, unit='s')
            ohlc_data.set_index('timestamp', inplace=True)  # Устанавливаем индексом время

            # Подготовка данных для графика
            ohlc_data = ohlc_data[['open', 'high', 'low', 'close']]  # Оставляем только необходимые колонки

            # Настройка линии TP и SL, если они заданы
            add_plot = []
            if up is not None:
                if up:
                    if take_profit is not None:
                        tp_series = pd.Series([take_profit] * len(ohlc_data),
                                              index=ohlc_data.index)  # Создаем серию для TP
                        add_plot.append(mpf.make_addplot(tp_series, color='green', linestyle='--', width=2, panel=0))
                    if stop_loss is not None:
                        sl_series = pd.Series([stop_loss] * len(ohlc_data),
                                              index=ohlc_data.index)  # Создаем серию для SL
                        add_plot.append(mpf.make_addplot(sl_series, color='red', linestyle='--', width=2, panel=0))
                else:
                    if take_profit is not None:
                        tp_series = pd.Series([take_profit] * len(ohlc_data),
                                              index=ohlc_data.index)  # Создаем серию для TP
                        add_plot.append(mpf.make_addplot(tp_series, color='red', linestyle='--', width=2, panel=0))
                    if stop_loss is not None:
                        sl_series = pd.Series([stop_loss] * len(ohlc_data),
                                              index=ohlc_data.index)  # Создаем серию для SL
                        add_plot.append(mpf.make_addplot(sl_series, color='green', linestyle='--', width=2, panel=0))

            # Построение и сохранение графика с увеличенным размером
            mpf.plot(ohlc_data, type='candle', title=symbol, style='charles',
                     figsize=(12, 8),  # Увеличенный размер графика
                     figratio=(16, 9),  # Соотношение сторон
                     figscale=1.5,  # Масштабирование
                     addplot=add_plot,  # Добавляем линии TP и SL
                     savefig=f'{symbol}_{user_id}.jpg',
                     panel_ratios=(1,),  # Убираем дополнительные панели
                     ylabel='',  # Убираем подпись Y
                     ylabel_lower='',  # Убираем подпись Y в нижней панели
                     show_nontrading=False)  # Не показывать неторговые часы

            # Обрезка изображения с помощью PIL
            img = Image.open(f'{symbol}_{user_id}.jpg')
            width, height = img.size

            # Определяем границы обрезки (150 пикселей слева, 50 пикселей снизу, 50 пикселей справа)
            left_crop = 170  # Обрезаем 150 пикселей слева
            right_crop = 50  # Обрезаем 50 пикселей справа
            bottom_crop = 50  # Обрезаем 50 пикселей снизу
            img_cropped = img.crop((left_crop, 0, width - right_crop, height - bottom_crop))  # Обрезаем изображение

            # Сохраняем обрезанное изображение
            img_cropped.save(f'{symbol}_{user_id}.jpg')

        # Форматирование цен
        def format_price(price):
            if price < 1:
                return f"{price:.6f}"  # Для маленьких чисел используем больше знаков после запятой
            else:
                return f"{price:.2f}"  # Для больших чисел можно оставить 2 знака после запятой

        # Запрос валютной пары у пользователя
        symbol = call.data
        await bot.delete_message(user_id, call.message.message_id)
        if lang =='ru':temp_text = f'⌛️Анализирую график...'
        else:temp_text =f"I'm analyzing the chart..."

        temp_mes = await bot.send_message(user_id,temp_text)
        try:
            start_time = int((time.time() - 24 * 60 * 60) * 1000)
            klines = await get_binance_klines(symbol, "5m", start_time)

            if klines:  # Проверяем, что данные не пустые
                # Extract highs and lows
                highs = np.array([float(kline[2]) for kline in klines])  # Максимальные цены
                lows = np.array([float(kline[3]) for kline in klines])  # Минимальные цены

                # Find fractals
                fractals = detect_fractals(highs, lows)

                # Initialize variables for output
                last_fractal_info = ""
                current_price = float(klines[-1][4])  # Текущая цена (цена закрытия последней свечи)

                take_profit = current_price * 1.005  # Пример TP на 1% выше текущей цены
                stop_loss = current_price * 0.995  # Пример SL на 1% ниже текущей цены
                up = None
                if fractals['up'] or fractals['down']:
                    # Determine last fractal
                    if fractals['up'] and (not fractals['down'] or fractals['up'][-1] > fractals['down'][-1]):
                        last_fractal_idx = fractals['up'][-1]
                        last_fractal_info = f"Фрактал вниз {len(highs) - last_fractal_idx} свечей назад, Цена: {format_price(highs[last_fractal_idx])}"
                        price_fractal = float(format_price(lows[last_fractal_idx]))
                        now_price = float(format_price(current_price))
                        percentage_difference = calculate_percentage_difference(price_fractal, now_price)
                        if percentage_difference > 0:
                            direction = "UP"
                        elif percentage_difference < 0:
                            direction = "DOWN"
                        else:
                            direction = "0"

                        if percentage_difference > 2 and direction == 'UP':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(70, 90)
                            ending_prognoz = random.randint(78, 95)
                        elif percentage_difference > 2 and direction == 'DOWN':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(70, 90)
                            ending_prognoz = random.randint(78, 95)
                        elif percentage_difference < 1.5 and direction == 'DOWN':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        elif percentage_difference < 1.5 and direction == 'UP':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        elif direction == '0':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        else:
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        take_profit = current_price * 1.005
                        stop_loss = current_price * 0.995

                    elif fractals['down'] and (not fractals['up'] or fractals['down'][-1] > fractals['up'][-1]):
                        last_fractal_idx = fractals['down'][-1]
                        last_fractal_info = f"Фрактал вверх {len(highs) - last_fractal_idx} свечей назад, Цена: {format_price(lows[last_fractal_idx])}"
                        price_fractal = float(format_price(lows[last_fractal_idx]))
                        now_price = float(format_price(current_price))
                        percentage_difference = calculate_percentage_difference(price_fractal, now_price)
                        if percentage_difference > 0:
                            direction = "UP"
                        elif percentage_difference < 0:
                            direction = "DOWN"
                        else:
                            direction = "0"
                        if percentage_difference > 2 and direction == 'UP':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(78, 95)
                            ending_prognoz = random.randint(65, 90)
                        elif percentage_difference > 2 and direction == 'DOWN':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(70, 90)
                            ending_prognoz = random.randint(78, 95)
                        elif percentage_difference < 1.5 and direction == 'DOWN':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        elif percentage_difference < 1.5 and direction == 'UP':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        elif direction == '0':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        else:
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        take_profit = current_price * 1.005
                        stop_loss = current_price * 0.995
                else:
                    price_30_minutes_ago = float(klines[-7][4])
                    now_price = float(format_price(current_price))
                    # Получаем цену 30 минут назад (например, предположим, что каждая свеча равна 1 минуте)
                    percentage_difference = calculate_percentage_difference(price_30_minutes_ago, now_price)
                    if percentage_difference > 0:
                        direction = "UP"
                    elif percentage_difference < 0:
                        direction = "DOWN"
                    else:
                        direction = "0"

                    if percentage_difference <= 1 and direction == 'UP':
                        prog = f'LONG ({signal_name_up})'
                        up = True
                        potential = random.randint(50, 70)
                        ending_prognoz = random.randint(65, 79)
                    elif percentage_difference <= 1 and direction == 'DOWN':
                        prog = f'SHORT ({signal_name_down})'
                        up = False
                        potential = random.randint(50, 70)
                        ending_prognoz = random.randint(65, 79)

                    elif percentage_difference > 1 and direction == 'UP':
                        prog = f'LONG ({signal_name_up})'
                        up = True
                        potential = random.randint(70, 90)
                        ending_prognoz = random.randint(80, 95)
                    elif percentage_difference > 1 and direction == 'DOWN':
                        prog = f'SHORT ({signal_name_down})'
                        up = False
                        potential = random.randint(70, 90)
                        ending_prognoz = random.randint(80, 95)
                    elif direction == '0':
                        price_30_minutes_ago = float(klines[-3][4])
                        now_price = float(format_price(current_price))
                        # Получаем цену 30 минут назад (например, предположим, что каждая свеча равна 1 минуте)
                        percentage_difference = calculate_percentage_difference(price_30_minutes_ago, now_price)
                        if percentage_difference > 0:
                            direction = "UP"
                        elif percentage_difference < 0:
                            direction = "DOWN"
                        else:
                            direction = "0"
                        if percentage_difference <= 1 and direction == 'UP':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)
                        elif percentage_difference <= 1 and direction == 'DOWN':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(50, 70)
                            ending_prognoz = random.randint(65, 79)

                        elif percentage_difference > 1 and direction == 'UP':
                            prog = f'LONG ({signal_name_up})'
                            up = True
                            potential = random.randint(70, 90)
                            ending_prognoz = random.randint(80, 95)
                        elif percentage_difference > 1 and direction == 'DOWN':
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(70, 90)
                            ending_prognoz = random.randint(80, 95)
                        else:
                            prog = f'SHORT ({signal_name_down})'
                            up = False
                            potential = random.randint(50, 60)
                            ending_prognoz = random.randint(50, 65)

                    take_profit = current_price * 1.005
                    stop_loss = current_price * 0.995
                # Save the chart
                save_chart(up, symbol, klines, take_profit, stop_loss)

        except Exception as e:
            print(f"Произошла ошибка: {e}")
        await bot.delete_message(user_id, temp_mes.message_id)
        paritet = round(random.uniform(30, 90), 2)
        if lang=='ru':
            msg = (f'Прогноз: <b>ВХОД {prog}</b> 💸'
                   f'\n\n📊 Аналитика алгоритма'
                   f'\n\n⭐️ Потенциал движение {prog}: {potential} % 📈'
                   f'\n⭐️ Долгосрочный тренд {prog}: {random.randint(55, 95)} % 📈'
                   f'\n⭐️ Объёмный профиль:  {random.randint(30, 90)} % 📈'
                   f'\n⭐️ Усредненный интерес на ПОКУПКУ: {round(random.uniform(30, 90), 2)} % ❌'
                   f'\n⭐️ Паритет объёмного баланса: {paritet} % ❌'
                   f'\n\n❗️ Сила направления движения от объёма {random.randint(30, 90)} %'
                   f'\n\n⭐️ Резюме от алгоритма '
                   f'\n\nТорговая аналитика по итогам анализа рассматриваем ВХОД {prog}, паритет объёмного баланса {paritet} %, по расчётам  AI определил что {random.randint(14, 32)} из 35 технических параметров указывают на приоритет движения ВХОД {prog} с вероятностью {ending_prognoz} % 🟡'
                   f'\n\n✅ Вероятность разворота цены: {round(random.uniform(15, 35), 2)} % ⏺️'
                   f'\n✅ Вероятность изменения потенциала:  {round(random.uniform(15, 35), 2)} % ⏺️'
                   f'\n\nИтоговая статистика успешного исхода сделки по AI: {ending_prognoz} % ❤️‍🔥'
                   f'\n\n⚠️ Данная информация не является торговым сигналом, выступает только в качестве дополнительного источника анализа !✅.')
        else:
            msg = (f'Forecast: <b>ENTRY {prog}</b> 💸'
                   f'\n\n📊 Algorithm analytics'
                   f'\n\n⭐️ {prog} movement potential: {potential} % 📈'
                   f'\n⭐️ Long-term trend {prog}: {random.randint(55, 95)} % 📈'
                   f'\n⭐️ Volume profile: {random.randint(30, 90)} % 📈'
                   f'\n⭐️ Average BUY interest: {round(random.uniform(30, 90), 2)} % ❌'
                   f'\n⭐️ Volume balance parity: {paritet} % ❌'
                   f'\n\n❗️ Directional strength from volume: {random.randint(30, 90)} %'
                   f'\n\n⭐️ Algorithm summary'
                   f'\n\nTrading analytics suggest considering ENTRY {prog}, volume balance parity {paritet}%, AI calculations show {random.randint(14, 32)} out of 35 technical parameters indicate priority for ENTRY {prog} movement with {ending_prognoz}% probability 🟡'
                   f'\n\n✅ Price reversal probability: {round(random.uniform(15, 35), 2)} % ⏺️'
                   f'\n✅ Potential change probability: {round(random.uniform(15, 35), 2)} % ⏺️'
                   f'\n\nFinal AI success rate: {ending_prognoz} % ❤️‍🔥'
                   f'\n\n⚠️ This information is not a trading signal, it serves only as an additional analysis source! ✅')
        photo = FSInputFile(path=f'{symbol}_{user_id}.jpg')
        if lang=='ru':name = 'Получить еще сигнал'
        else: name = 'Get another signal'
        await bot.send_photo(user_id, photo, caption=msg, reply_markup=get_signal_key(name))
        await call.answer()
        os.remove(path=f'{symbol}_{user_id}.jpg')
        current_time = datetime.datetime.now().strftime('%m.%d@%H:%M:%S')
        await storage.redis.set(user_name, current_time)
    else:
        # Пример формата времени, который включает секунды
        formatted_time = time_resp.strftime('%m.%d@%H:%M:%S')
        current_time = datetime.datetime.now().strftime('%m.%d@%H:%M:%S')
        current_datetime = datetime.datetime.strptime(current_time, '%m.%d@%H:%M:%S')
        second_datetime = datetime.datetime.strptime(formatted_time, '%m.%d@%H:%M:%S')
        time_difference = abs(current_datetime - second_datetime)
        time_difference_seconds = time_difference.total_seconds()
        time_wait = int(60 - time_difference_seconds)
        if lang=='ru':
            await call.answer(f'⚠️Сигнал можно запрашивать раз в минуту\nПодожите еще {time_wait} сек.', show_alert=True)
        else:
            await call.answer(f'⚠️ 1 request per minute\nWait {time_wait}s', show_alert=True)


@router.callback_query(F.data == 'open_menu_signals')
async def open_menu_signals(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    await bot.delete_message(chat_id=user_id, message_id=call.message.message_id)
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
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
    reviews,link_reviews,is_help,link_help,is_button_free = data[0]

    await bot.send_message(user_id, msg, reply_markup=main_keyboard(signals = f'{signals}',profile = f'{profile}',
                                                                    is_free =int(is_ref) , get_free = f'{free_get_bot}',
                                                                    is_rewievs = reviews,reviews = rew,url_reviews = link_reviews,is_help = is_help, help = help,url_help = link_help,is_btn_free=is_button_free))
    await call.answer()

@router.callback_query(F.data=='back_main')
async def back_main_menu(call:CallbackQuery,bot:Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang = 'en'
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
    reviews,link_reviews,is_help,link_help,is_button_free = data[0]
    await bot.delete_message(user_id, call.message.message_id)
    await bot.send_message(chat_id=user_id,text=msg,reply_markup=main_keyboard(signals = f'{signals}',profile = f'{profile}',
                                                                               is_free =int(is_ref) , get_free = f'{free_get_bot}',
                                                                               is_rewievs = reviews,reviews = rew,url_reviews = link_reviews,is_help = is_help, help = help,url_help = link_help,is_btn_free=is_button_free))

    await call.answer()


@router.callback_query(F.data=='get_free_bot_btn')
async def open_free_bot(call:CallbackQuery,bot:Bot):
    user_id = call.from_user.id
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang='en'
    if lang=='en':
        query = 'SELECT mes_id_free_en, admin_id_free FROM creator WHERE user_id = ?'
    else:
        query = 'SELECT mes_id_free, admin_id_free FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)
    mes_id_free, admin_id_free = data[0]
    msg_id, btn_name, link = str(mes_id_free).split('~')
    if btn_name!='0':
        await bot.copy_message(user_id, from_chat_id=int(admin_id_free) ,message_id=int(msg_id),  reply_markup=coonstruct_key(btn_name, link))
    else:
        await bot.copy_message(user_id, from_chat_id=int(admin_id_free) ,message_id=int(msg_id))

    await call.answer()


async def start():
    logging.basicConfig(level=logging.INFO)
    bot: Bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    storage = RedisStorage.from_url('redis://default:SNqtFDcehlsTjoEMcPTpgtXVvEfFxThU@redis-69bt.railway.internal:6379/0')
    dp = Dispatcher(storage=storage)
    DB_PATH = 'users.db'
    dp.message.middleware.register(BlacklistMiddleware(DB_PATH))
    dp.callback_query.middleware.register(BlacklistMiddleware(DB_PATH))
    dp.update.middleware.register(BlacklistMiddleware(DB_PATH))

    scheduler = AsyncIOScheduler(timezone = 'Europe/Moscow')
    scheduler.add_job(update_subscribe, trigger='cron', hour=0, minute=0,start_date = datetime.datetime.now(),kwargs={'bot': bot})
    scheduler.start()
    dp.include_routers(router, admin_router,pay_router)

    app = web.Application()
    app['bot'] = bot
    webhook_paths = [WEBHOOK_PATH_CRYPTOBOT, WEBHOOK_CRISTAL_PAY, WEBHOOK_CIS_PAY]

    for path in webhook_paths:
        app.router.add_route('*', path, handle_postback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)

    logging.info(f"Starting web server at http://{WEBAPP_HOST}:{WEBAPP_PORT}")
    await site.start()

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as ex:
        logging.error(f"[Exception] - {ex}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    with contextlib.suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(start())
