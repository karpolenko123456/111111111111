import datetime
from datetime import timedelta
import requests
from aiocryptopay import AioCryptoPay, Networks
from aiogram import Bot, Router, F
from aiogram.types import  Message, CallbackQuery, TelegramObject, LabeledPrice, PreCheckoutQuery
import config
from aiogram.fsm.context import FSMContext

from db import execute_query
from keyboards import bot_pay_key, StepsForm, cancel_pay_back_key, back_fter_pay_key

router = Router()

@router.callback_query(F.data.startswith('cryptobot_pay'))
async def open_crypto_bot_pay(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)
    lang = call.from_user.language_code
    data = await state.get_data()
    sum_pay = data.get('summ_pay')
    crypto = AioCryptoPay(token=config.token_cryptobot, network=Networks.MAIN_NET)
    fiat_invoice = await crypto.create_invoice(amount=int(sum_pay), fiat='USD',currency_type='fiat',expires_in=600)
    invoice_url = fiat_invoice.bot_invoice_url
    invoice_id = fiat_invoice.invoice_id
    query = 'UPDATE users SET invoice_id = ? WHERE user_id = ?'
    params = (invoice_id, user_id)
    await execute_query(query, params, True, 0)
    if lang!='ru' and lang!='en': lang='en'
    if call.data=='cryptobot_pay': is_menu=1
    else: is_menu=0
    if lang=='ru':
        mes_pay = await bot.send_message(user_id, f"📎<b>Перейдите по <a href='{invoice_url}'>ссылке</a> для оплаты {sum_pay}$</b>\n🤖После пополнения Бот автоматически проверит Ваш платеж."
                                        f"\n\nℹ️<i>Ссылка для оплаты действительна 10 минут после создания</i>",disable_web_page_preview=True,
                               reply_markup=bot_pay_key('Оплатить',invoice_url,is_menu))
    else:
        mes_pay = await bot.send_message(
            user_id,
            f"📎<b>Click the <a href='{invoice_url}'>link</a> to pay {sum_pay}$</b>\n🤖After payment, the Bot will automatically verify your transaction."
            f"\n\nℹ️<i>The payment link is valid for 10 minutes after creation</i>",
            disable_web_page_preview=True,
            reply_markup=bot_pay_key('Pay Now', invoice_url,is_menu))

    await execute_query(f'UPDATE users SET mes_pay_id = ? WHERE user_id = ?', (mes_pay.message_id, user_id), True, 0)

    await crypto.close()
    await state.clear()

@router.callback_query(F.data.startswith('crystal_pay'))
async def open_crystal_pay(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)
    data = await state.get_data()
    sum_pay = data.get('summ_pay')
    lang = call.from_user.language_code

    if lang!='ru' and lang!='en': lang='en'
    # if lang=='en':
    #     cur = 'USD'
    # else:
    #     cur='RUB'
    url = "https://api.crystalpay.io/v3/invoice/create/"
    headers = {
        "Content-Type": "application/json"
    }
    extra = f'{user_id}'
    sum_pay = int(sum_pay)
    data = {
        "auth_login": "dendi0110",
        "auth_secret": "aba116eeb7175a8fb50905a7f33317eeff463c9f",
        'amount':sum_pay,
        'type':'purchase',
        'lifetime':10,
        'amount_currency':'USD',
        'extra':extra,
        'redirect_url':'https://t.me/MasonsFX_bot',
        'callback_url':'https://195.2.79.111/cristal_pay'

    }
    # 'callback_url':''
    response = requests.post(url, headers=headers, json=data)
    url = response.json().get('url')
    print(response.json())


    if call.data=='crystal_pay': is_menu=1
    else:is_menu=0


    if lang=='ru':
        mes_pay = await bot.send_message(user_id, f"📎<b>Перейдите по <a href='{url}'>ссылке</a> для оплаты {sum_pay}$</b>\n🤖После пополнения Бот автоматически проверит Ваш платеж."
                                        f"\n\nℹ️<i>Ссылка для оплаты действительна 10 минут после создания</i>",disable_web_page_preview=True,
                               reply_markup=bot_pay_key('Оплатить',url,is_menu))
    else:
        mes_pay = await bot.send_message(
            user_id,
            f"📎<b>Click the <a href='{url}'>link</a> to pay {sum_pay}$</b>\n🤖After payment, the Bot will automatically verify your transaction."
            f"\n\nℹ️<i>The payment link is valid for 10 minutes after creation</i>",
            disable_web_page_preview=True,
            reply_markup=bot_pay_key('Pay Now', url,is_menu))
    await execute_query(f'UPDATE users SET mes_pay_id = ? WHERE user_id = ?', (mes_pay.message_id, user_id), True, 0)

@router.callback_query(F.data.startswith('cis_pay'))
async def open_cis_pay(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    await bot.delete_message(user_id, call.message.message_id)
    data = await state.get_data()
    sum_pay = data.get('summ_pay')
    lang = call.from_user.language_code

    if lang!='ru' and lang!='en': lang='en'

    url = "https://api.monee.pro/payment/create"
    headers = {
        "Content-Type": "application/json"
    }

    comment = str(user_id)
    if int(sum_pay)==99:
        sum_pay_new=9000.00
    elif int(sum_pay)==499:
        sum_pay_new=45000.00
    elif int(sum_pay)==799:
        sum_pay_new=72000.00

    data = {
        "shop_to": "6b53e04e-cf2c-4ca4-b2e5-3f1d79ff463c",
        "sum": sum_pay_new,
        "comment": 'Subscribe private bot',
        "custom_fields":comment,
        "hook_url":'https://195.2.79.111/cis_pay',
        "expire": 10,
        "success_url": "https://t.me/MasonsFX_bot",
        "subtract": 1
    }

    # "hook_url": "https://cispay.pro/hook",
    response = requests.post(url, headers=headers, json=data)
    url = response.json().get('url')
    print(response.json())


    if call.data=='cis_pay': is_menu=1
    else:is_menu=0

    if lang=='ru':
        mes_pay = await bot.send_message(user_id, f"📎<b>Перейдите по <a href='{url}'>ссылке</a> для оплаты {sum_pay}$</b>\n🤖После пополнения Бот автоматически проверит Ваш платеж."
                                        f"\n\nℹ️<i>Ссылка для оплаты действительна 10 минут после создания</i>",disable_web_page_preview=True,
                               reply_markup=bot_pay_key('Оплатить',url,is_menu))
    else:
        mes_pay = await bot.send_message(
            user_id,
            f"📎<b>Click the <a href='{url}'>link</a> to pay {sum_pay}$</b>\n🤖After payment, the Bot will automatically verify your transaction."
            f"\n\nℹ️<i>The payment link is valid for 10 minutes after creation</i>",
            disable_web_page_preview=True,
            reply_markup=bot_pay_key('Pay Now', url,is_menu))

    await execute_query(f'UPDATE users SET mes_pay_id = ? WHERE user_id = ?', (mes_pay.message_id, user_id), True, 0)

@router.callback_query(F.data.startswith('ammer_pay'))
async def open_ammer_pay(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    sum_pay = data.get('summ_pay')
    subscr = ''
    if int(sum_pay)==99:subscr='month'
    if int(sum_pay)==499:subscr='six'
    if int(sum_pay)==799:subscr='year'
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang='en'
    if lang=='en':
        title = 'Subscribe to the bot'
        description = '📊Access to a private bot with signals for trading on the stock exchange'
        pay = 'Pay'
    else:
        title = 'Подписка на бота'
        description = '📊Доступ к приватному боту с сигналами для торговли на бирже'
        pay = 'Оплатить'
    await bot.delete_message(user_id,call.message.message_id)

    if call.data=='ammer_pay': is_menu=1
    else:is_menu=0
    sum_pay = int(sum_pay)*100
    print(sum_pay)
    await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=description,
        payload=f'ammer_pay_{subscr}',
        provider_token='5775769170:LIVE:TG_FbvchXlj1DSNLAg1927peY4A',
        currency='USD',
        prices=[
            LabeledPrice(
                label='Subscribe',
                amount=sum_pay
            )
        ],
        start_parameter='MasonsFX_bot',
        request_timeout=10,
        reply_markup=cancel_pay_back_key(f'{pay}',is_menu)
    )
    await call.answer()

@router.pre_checkout_query()
async def pre_check_out_ammer_pay(query:PreCheckoutQuery,bot:Bot):
    payload = query.invoice_payload
    await bot.answer_pre_checkout_query(query.id, ok=True)
    if 'ammer_pay' in payload:
        await bot.answer_pre_checkout_query(query.id, ok=True)
    elif 'another_payment_system' in payload:
        await bot.answer_pre_checkout_query(query.id, ok=True)

@router.message(F.successful_payment)
async def succesful_payment_ammer_pay(message: Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    payload = message.successful_payment.invoice_payload
    subscr = str(payload).split('_')[2]

    if lang != 'ru' and lang != 'en': lang = 'en'

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
    if subscr == 'month':
        days_to_add = 30
    elif subscr == 'six':
        days_to_add = 180
    elif subscr == 'year':
        days_to_add = 365

    # Если подписка уже активна
    if date_end_sub:
        # Проверим, если дата окончания подписки еще не наступила
        if date_end_sub > str_time:
            # Добавляем нужное количество дней к дате окончания подписки
            new_end_date = datetime.datetime.strptime(date_end_sub, "%Y-%m-%d %H:%M:%S") + timedelta(days=days_to_add)
        else:
            # Если подписка уже закончена, устанавливаем новую дату на основе текущей
            new_end_date = now + datetime.timedelta(days=days_to_add)
    else:
        # Если дата окончания подписки пустая или равна нулю, устанавливаем новую дату на основе текущей
        new_end_date = now + timedelta(days=days_to_add)

    # Обновляем дату окончания подписки в базе данных
    update_query = 'UPDATE users SET date_end_sub = ?,sub_name = ? WHERE user_id = ?'
    params = (new_end_date.strftime("%Y-%m-%d %H:%M:%S"),subscr, user_id)
    await execute_query(update_query, params, True, 0)

    # Сообщение пользователю
    if 'ammer_pay' in payload:
        if lang == 'ru':
            msg = (f'✅Счет успешно оплачен на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency}.'
                   f'\n\n<b>🔔Вы успешно продлили подписку до {new_end_date.strftime("%Y-%m-%d %H:%M:%S")}</b>')
            await message.answer(msg, reply_markup=back_fter_pay_key())
        else:
            msg = (f'✅The payment was successfully made for {message.successful_payment.total_amount // 100} {message.successful_payment.currency}.'
                   f'\n\n<b>🔔You have successfully extended your subscription until {new_end_date.strftime("%Y-%m-%d %H:%M:%S")}</b>')
            await message.answer(msg, reply_markup=back_fter_pay_key())

    elif 'smart_pay' in payload:
        if lang == 'ru':
            msg = (f'✅Счет успешно оплачен на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency}.'
                   f'\n\n<b>🔔Вы успешно продлили подписку до {new_end_date.strftime("%Y-%m-%d %H:%M:%S")}</b>')
            await message.answer(msg)
        else:
            msg = (f'✅The payment was successfully made for {message.successful_payment.total_amount // 100} {message.successful_payment.currency}.'
                   f'\n\n<b>🔔You have successfully extended your subscription until {new_end_date.strftime("%Y-%m-%d %H:%M:%S")}</b>')
            await message.answer(msg, reply_markup=back_fter_pay_key())



@router.callback_query(F.data.startswith('smart_pay'))
async def open_smart_pay(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    sum_pay = data.get('summ_pay')
    subscr = ''
    if int(sum_pay)==99:subscr='month'
    if int(sum_pay)==499:subscr='six'
    if int(sum_pay)==799:subscr='year'
    lang = call.from_user.language_code
    if lang!='ru' and lang!='en': lang='en'
    await bot.delete_message(user_id,call.message.message_id)
    if lang=='en':
        title = 'Subscribe to the bot'
        description = '📊Access to a private bot with signals for trading on the stock exchange'
        pay = 'Pay'
    else:
        title = 'Подписка на бота'
        description = '📊Доступ к приватному боту с сигналами для торговли на бирже'
        pay = 'Оплатить'

    if call.data=='smart_pay': is_menu=1
    else:is_menu=0

    await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=description,
        payload=f'smart_pay_{subscr}',
        provider_token='1725141586:TEST:313dda9e7865d0117b2ee7e33f85ae02c8717e6b',
        currency='USD',
        prices=[
            LabeledPrice(
                label='Subscribe',
                amount=10
            )
        ],
        start_parameter='MasonsFX_bot',
        request_timeout=10,
        reply_markup=cancel_pay_back_key(f'{pay}',is_menu)
    )
    await call.answer()

