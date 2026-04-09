#!/usr/bin/env python3
import datetime
import random

import aiosqlite
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatJoinRequest, Message, CallbackQuery, TelegramObject, InputMediaPhoto, InputMedia, \
    KeyboardButtonRequestUsers
import asyncio
from aiogram import Bot, Dispatcher, Router, F
import sqlite3
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import config
from keyboards import StepsForm

router = Router()


def create_users_table():
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS creator (user_id INTEGER PRIMARY KEY, ref_link TEXT DEFAULT '0', check_subscr INTEGER DEFAULT 1, mes_auto_send TEXT DEFAULT '0')''')
        conn.commit()
        conn.close()
        print('таблица создана')
    except Exception as e:
        print(f"ОШИБКА {e}")

def cancel_sending():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'❌Отменить', callback_data=f'cancel_send_reg')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def black_list_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'Восстановить всех', callback_data=f'delete_all')
    key_build.button(text=f'❌Отменить', callback_data=f'cancel_send_reg')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def sending_black_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'ДА', callback_data=f'sending_black')
    key_build.button(text=f'НЕТ', callback_data=f'no_sending_black')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def button_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'Добавить кнопку', callback_data=f'add_button')
    key_build.button(text=f'Пропустить', callback_data=f'skip_button')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)


def send_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'✅Рассылка всем юзерам', callback_data=f'start_sending_all')
    key_build.button(text=f'❌Отменить рассылку', callback_data=f'cancel_sending')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

# def buttons_sett_key(help_status,rev_status, wallet_status, stars_status, crystal_status,
#                      data1,data2, data3, data4, data5):
#     key_build = InlineKeyboardBuilder()
#     key_build.button(text=f'{help_status}Кнопка Помощь', callback_data=f'{data1}')
#     key_build.button(text=f'{rev_status}Кнопка Отзывы', callback_data=f'{data2}')
#     key_build.button(text=f'{wallet_status}TG Wallet', callback_data=f'{data3}')
#     key_build.button(text=f'{stars_status}TG Stars', callback_data=f'{data4}')
#     key_build.button(text=f'{crystal_status}Crystal Pay', callback_data=f'{data5}')
#     key_build.button(text=f'Ссылка Помощь', callback_data=f'edit_help_link')
#     key_build.button(text=f'Ссылка отзывы', callback_data=f'edit_rew_link')
#     key_build.adjust(2,2,1,1,1)
#     return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)


def send_black_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'💀Рассылка юзерам из ЧС', callback_data=f'start_sending_chs')
    key_build.button(text=f'❌Отменить рассылку', callback_data=f'cancel_sending')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def add_btn_free_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'Добавить кнопку', callback_data=f'add_btn_free_mess')
    key_build.button(text=f'Пропустить', callback_data=f'no_btn_free_mess')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def date_period_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'1 день', callback_data=f'day_1')
    key_build.button(text=f'7 дней', callback_data=f'day_7')
    key_build.button(text=f'30 дней', callback_data=f'day_30')
    key_build.button(text=f'60 дней', callback_data=f'day_60')
    key_build.button(text=f'90 дней', callback_data=f'day_90')
    key_build.button(text=f'120 дней', callback_data=f'day_120')
    key_build.button(text=f'Год', callback_data=f'day_365')
    key_build.button(text=f'Доступ навсегда', callback_data=f'infiniti')
    key_build.button(text=f'❌Отмена', callback_data=f'cancel_edit')
    key_build.adjust(3,3,1,1,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)


def coonstruct_key(text, url):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{text}', url=f'{url}')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def admin_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'👨🏿‍🦰Количество юзеров', callback_data=f'users_amount')
    key_build.button(text=f'💌Рассылка юзерам', callback_data=f'sending_rega')
    key_build.button(text=f'☎️Включить проверку подписки', callback_data=f'on_sub')
    key_build.button(text=f'📵Выключить проверку подписки', callback_data=f'off_sub')
    key_build.button(text=f'🔄Обновить канал для подписки', callback_data=f'refresh_channel')
    key_build.button(text=f'⚙️Добавить администратора', callback_data=f'add_admin')
    key_build.button(text=f'💠Выдать доступ пользователю', callback_data=f'get_user_access')
    key_build.button(text=f'Отключить/Включить кнопки', callback_data=f'buttons_turn_on_off')
    key_build.adjust(1,1,1,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def cancel_admin_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'❌Отмена', callback_data=f'cancel_edit')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def admin_butt_key():
    key_build = ReplyKeyboardBuilder()
    key_build.button(text=f'/admin')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

@router.message(F.text == '/admin')
async def start_admin_menu(message: Message,bot: Bot,state: FSMContext):
    user_id = message.from_user.id
    adm_id = config.admin_id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM creator')
    data = cursor.fetchall()
    admin_list = [item for sublist in data for item in sublist]
    print(admin_list)
    conn.commit()
    conn.close()
    if user_id in admin_list or user_id == adm_id:
        msg = f'<b>Это меню администратора</b>'
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO creator (user_id) VALUES (?)', (user_id,))
        await bot.send_message(user_id, msg, reply_markup=admin_key())
        await state.clear()
        conn.commit()
        conn.close()

@router.callback_query(F.data == 'add_admin')
async def add_admin(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    msg = f'Отправьте ID Телеграмма администратора.'
    await state.set_state(StepsForm.wait_id_admin)
    await bot.send_message(user_id,msg,reply_markup=cancel_sending())
    await call.answer()

@router.message(StepsForm.wait_id_admin)
async def save_admin_id(message:Message,bot:Bot,state:FSMContext):
    user_id = message.from_user.id
    msg = f'Администратор успешно добавлен!'
    id_admin = message.text
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO creator (user_id) VALUES (?)', (id_admin,))
        conn.commit()
        conn.close()
        await bot.send_message(user_id,msg)
        await state.clear()
    except:
        await message.answer_dice('⚠️Произошла ошибка, отправьте ID администратора еще раз!')


def add_admin_key():
    request_id = random.randint(1, 10000000)
    req_users = KeyboardButtonRequestUsers(request_id=request_id, user_is_bot=False)
    key_build = ReplyKeyboardBuilder()
    key_build.button(text=f'Выбрать пользователя', request_users=req_users)
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = True)


@router.callback_query(F.data=='get_user_access')
async def get_user_access(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    await bot.send_message(call.from_user.id, f'💠Нажмите кнопку <b>Выбрать пользователя</b> и отправьте боту пользователя, которому нужно выдать доступ.', reply_markup=add_admin_key())
    await state.set_state(StepsForm.wait_user_acces)
    await call.answer()

@router.message(StepsForm.wait_user_acces)
async def choise_date_add_user(message:Message,bot:Bot,state:FSMContext):
    add_user_id = message.user_shared.user_id
    msg = f'📅Выберите период предоставления доступа.'
    await message.answer(msg, reply_markup=date_period_key())
    await state.update_data(add_user_id = add_user_id)

@router.callback_query(F.data.in_(['day_1', 'day_7', 'day_30', 'day_60', 'day_90', 'day_120', 'day_365', 'infiniti']))
async def save_user_access(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    amount_days = str(call.data).split('_')[1]
    data = await state.get_data()
    add_user_id = data.get('add_user_id')
    now = datetime.datetime.now()
    str_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # Запросим текущие данные пользователя
    query = 'SELECT date_start_sub, date_end_sub FROM users WHERE user_id = ?'
    params = (user_id,)
    date = await execute_query(query, params, False, 2)

    date_start_sub, date_end_sub = date[0] if date else (None, None)

    days_to_add = int(amount_days)


    if date_end_sub:
        if date_end_sub > str_time:
            new_end_date = datetime.datetime.strptime(date_end_sub, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=days_to_add)
        else:
            new_end_date = now + datetime.timedelta(days=days_to_add)
    else:

        new_end_date = now + datetime.timedelta(days=days_to_add)

    # Обновляем дату окончания подписки в базе данных
    update_query = 'UPDATE users SET date_start_sub = ?,date_end_sub = ?,sub_name = ? WHERE user_id = ?'
    params = (str_time, new_end_date.strftime("%Y-%m-%d %H:%M:%S"),'month', int(add_user_id))
    await execute_query(update_query, params, True, 0)

    if call.data in ['day_1', 'day_7', 'day_30', 'day_60', 'day_90', 'day_120', 'day_365']:
        msg = f'✅Доступ пользователю предоставлен на {amount_days} дней.'
        await bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id)
    else:
        msg = f'✅Доступ пользователю предоставлен навсегда.'
        await bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id)



def aprove_delete_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'Да,подтверждаю', callback_data=f'aprove_delete_black')
    key_build.button(text=f'Нет, хочу отменить', callback_data=f'cancel_send_reg')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)



@router.callback_query(F.data == 'delete_black')
async def delete_black_list(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(user_id) FROM black_list')
    users = cursor.fetchone()[0]
    msg = (f'Меню управления черным списком.'
           f'\nЕсли вы хотите убрать всех пользователей из черного списка нажмите "Восстановить всех"'
           f'\nЕсли вы хотите убрать только 1 юзера отправьте его ID в чат.'
           f'\n\nКоличество юзеров в черном списке - {users}')
    black_mess = await bot.send_message(user_id,msg,reply_markup=black_list_key())
    await state.set_state(StepsForm.wait_id_black)
    await state.update_data(black_mess = black_mess.message_id)
    await call.answer()
    conn.commit()
    conn.close()

@router.message(StepsForm.wait_id_black)
async def delete_one_user(message:Message,bot:Bot,state:FSMContext):
    user_id = message.from_user.id
    msg = (f'Убрал юзера из черного списка!\nВы хотите направить ему сообщение через бота?')
    black_id = int(message.text)
    data = await state.get_data()
    black_mess = data.get('black_mess')
    await bot.edit_message_reply_markup(user_id, black_mess, reply_markup=None)
    black_list = [black_id]
    await state.update_data(black_list = black_list)
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM black_list WHERE user_id = ?', (black_id,))
        conn.commit()
        conn.close()
        await bot.send_message(user_id, msg,reply_markup=sending_black_key())
    except Exception as e:
        print(e)
        await message.answer('❌Ошибка удаления! Направьте еще раз ID пользователя.')

@router.callback_query(F.data == 'delete_all')
async def delete_black_all(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    msg = f'Вы уверены, что хотите удалить всех пользователей из черного списка?'
    await bot.edit_message_text(str(msg), int(user_id), int(call.message.message_id), reply_markup=aprove_delete_key())


@router.callback_query(F.data == 'aprove_delete_black')
async def aprove_delete_black(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id  = call.from_user.id
    if call.data == 'aprove_delete_black':
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM black_list')
        all_users = cursor.fetchall()
        users_list = [item for sublist in all_users for item in sublist]
        await state.update_data(black_list = users_list)
        cursor.execute('DELETE FROM black_list')
        conn.commit()
        conn.close()
        msg = (f'Убрал всех юзеров из черного списка!\nВы хотите сделать рассылку по ним через бота?')
        await bot.edit_message_text(str(msg),int(user_id), int(call.message.message_id), reply_markup=sending_black_key())



@router.callback_query(F.data.in_(['sending_black', 'no_sending_black']))
async def get_sending_black(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    if call.data=='sending_black':
        await bot.delete_message(user_id, call.message.message_id)
        msg = f'📝Ожидаю сообщение для рассылки!'
        await bot.send_message(call.from_user.id, msg,reply_markup=cancel_sending())
        await state.set_state(StepsForm.wait_mes_for_send)
    elif call.data=='no_sending_black':
        await bot.delete_message(user_id, call.message.message_id)
        await bot.send_message(user_id,f'✅Пользователи успешно удалены из черного списка, рассылка отменена!')
    await call.answer()




@router.callback_query(F.data == 'users_amount')
async def amount_users(call: CallbackQuery,bot:Bot):
    user_id = call.from_user.id
    # Получаем текущую дату и время
    now = datetime.datetime.now()


    # Определяем временные промежутки
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - datetime.timedelta(days=1)
    week_start = today_start - datetime.timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Запросы для подсчета пользователей
    query_today = """
        SELECT COUNT(*) FROM users 
        WHERE add_date >= ?
    """
    query_yesterday = """
        SELECT COUNT(*) FROM users 
        WHERE add_date >= ? AND add_date < ?
    """
    query_week = """
        SELECT COUNT(*) FROM users 
        WHERE add_date >= ? 
    """



    # Выполняем запросы
    today_users = await execute_query(query_today, (today_start,),False, 1)
    yesterday_users = await execute_query(query_yesterday, (yesterday_start, today_start), False, 1)
    week_users = await execute_query(query_week, (week_start,), False, 1)

    query = 'SELECT all_sum_deposit FROM creator WHERE user_id = ?'
    params = (config.admin_id,)
    all_dep = await execute_query(query,params,False,1)
    all_dep = all_dep[0]


    query = 'SELECT COUNT(user_id) FROM users'
    params = ()
    data_all = await execute_query(query, params, False, 1)
    all_users = data_all[0]




    # Формируем сообщение с результатами
    message = (
        f"📊<b>Пользователи:</b> {all_users}\n"
        f"<b>├Сегодня:</b> {today_users[0] if today_users else 0}\n"
        f"<b>├Вчера:</b> {yesterday_users[0] if yesterday_users else 0}\n"
        f"<b>├На этой неделе:</b> {week_users[0] if week_users else 0}\n"
        f"\n<b>💰Всего пополнений:</b> {round(all_dep,2)}$"
    )

    # Отправляем сообщение пользователю
    await bot.send_message(chat_id=user_id, text=message)
    await call.answer()

@router.callback_query(F.data == 'refresh_channel')
async def refresh_channel(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    msg = f'Отправьте ссылку на канал для подписки.'
    await bot.send_message(user_id, msg,reply_markup=cancel_sending())
    await state.set_state(StepsForm.wait_link_sub)
    await call.answer()

@router.message(StepsForm.wait_link_sub)
async def write_channel_link(message:Message,state:FSMContext):
    link = message.text
    msg = f'Записал ссылку на канал, а теперь перешлите любой пост с вашего канала.'
    await message.answer(msg, reply_markup=cancel_sending())
    await state.update_data(link = link)
    await state.set_state(StepsForm.wait_forward_mes)

@router.message(StepsForm.wait_forward_mes)
async def save_channel_id(message:Message,state:FSMContext):
    if message.forward_from_chat:
        id_channel = message.forward_from_chat.id
        data=await state.get_data()
        link = data.get('link')
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE creator SET channel_id = ?, channel_link = ? WHERE user_id = ?', (id_channel,link, config.admin_id))
            conn.commit()
            conn.close()

            msg = (f'✅Записал данные!'
                   f'\nНе забудь добавить бота в администраторы канала!')
            await message.answer(msg)
            await state.clear()
        except Exception as e:
            await message.answer('❌Произошла ошибка! Перешлите пост с канала еще раз.',reply_markup=cancel_sending())

@router.callback_query(F.data == 'get_unlock')
async def get_dost(call:CallbackQuery,bot:Bot,state:FSMContext):
    await bot.send_message(call.from_user.id, f'Отправьте ID Телеграмм юзера, которому нужен доступ в бота',reply_markup=cancel_sending())
    await state.set_state(StepsForm.wait_id)
    await call.answer()

@router.message(StepsForm.wait_id)
async def write_dost(message:Message,bot:Bot,state:FSMContext):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET platform_id = 12345678, is_deposit = 1, sum_deposit = 100 WHERE user_id = ?', (int(message.text),))
        conn.commit()
        await message.answer('✅Доступ успешно предоставлен.')
    except:
        await message.answer('⚠️Произошла ошибка при добавлении доступа. Возможно пользователь не запустил бота или вы указали неверный id.')
    conn.close()
    await state.clear()

@router.callback_query(F.data == 'update_links_ru')
async def update_ref_link(call:CallbackQuery,bot:Bot, state: FSMContext):
    user_id = call.from_user.id
    msg = (f'<b>Отправьте новую реферальную ссылку</b>')
    await state.set_state(StepsForm.wait_ref_link)
    await bot.send_message(user_id, msg)
    await call.answer()

@router.message(StepsForm.wait_ref_link)
async def save_new_link(message: Message,bot: Bot,state: FSMContext):
    link = message.text
    adm_id = config.admin_id
    user_id = message.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE creator SET ref_link = ? WHERE user_id = ?',(link, adm_id))
        conn.commit()
        await bot.send_message(user_id, f'Новая реф. ссылка успешно добавлена')
        await state.clear()
    except:
        await bot.send_message(user_id, f'⚠️Произошла ошибка при добавлении ссылки, направьте ссылку еще раз в чат')

    conn.close()




@router.callback_query(F.data == 'sending_rega')
async def send_users_reg(call: CallbackQuery, bot: Bot, state: FSMContext):
    msg = f'📝Ожидаю сообщение для рассылки!'
    await bot.send_message(call.from_user.id, msg,reply_markup=cancel_sending())
    await state.set_state(StepsForm.wait_mes_for_send)
    await call.answer()

@router.message(StepsForm.wait_mes_for_send)
async def get_button_for_send(message: Message, bot: Bot, state: FSMContext):
    id = message.message_id
    user_id = message.from_user.id
    await bot.send_message(user_id, f'✅Принял ваше сообщение. '
                                    f'\n\n\rНажмите Добавить кнопку либо Пропустить, если кнопка не нужна',reply_markup=button_key())
    await state.update_data(id = id)

@router.callback_query(F.data == 'add_button')
async def add_buttons(call: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    user_id = call.from_user.id
    msg = '🔤Отправьте текст кнопки.'
    await bot.send_message(user_id, msg, reply_markup=cancel_sending())
    await state.set_state(StepsForm.wait_text_button)
    await call.answer()

@router.message(StepsForm.wait_text_button)
async def get_text_button(message: Message, bot: Bot, state: FSMContext):
    text_button = message.text

    user_id = message.from_user.id
    msg = ('✅Записал текст кнопки!'
           '\n\n📎Теперь отправьте ссылку')
    await bot.send_message(user_id, msg, reply_markup=cancel_sending())
    await state.set_state(StepsForm.wait_url_button)
    await state.update_data(text_button = text_button)

@router.message(StepsForm.wait_url_button)
async def get_chek_mes_button_send(message: Message, bot: Bot, state: FSMContext):
    url = message.text
    user_id = message.from_user.id
    await state.update_data(url = url)
    data = await state.get_data()
    id_mes = data.get('id')
    text_button = data.get('text_button')
    users_black = data.get('black_list')
    if users_black:
        await bot.send_message(user_id, f'✅Запомнил ссылку'
                                        f'\n\n\rВаше сообщение для рассылки отправил ниже.'
                                        f'\n\n\rЕсли все правильно нажмите 💀Рассылка юзерам из ЧС, если нет - ❌Отменить',reply_markup=send_black_key())
        await bot.copy_message(user_id, user_id, message_id=id_mes, reply_markup=coonstruct_key(text_button,url))
    elif users_black==None:
        await bot.send_message(user_id, f'✅Запомнил ссылку'
                                        f'\n\n\rВаше сообщение для рассылки отправил ниже.'
                                        f'\n\n\rЕсли все правильно нажмите ✅Начать рассылку, если нет - ❌Отменить',reply_markup=send_key())
        await bot.copy_message(user_id, user_id, message_id=id_mes, reply_markup=coonstruct_key(text_button,url))

@router.callback_query(F.data == 'skip_button')
async def check_msg_no_button(call: CallbackQuery, bot: Bot,state: FSMContext):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    user_id = call.from_user.id

    data = await state.get_data()
    id_mes = data.get('id')
    users_black = data.get('black_list')
    if users_black:
        await bot.send_message(user_id, f'✅Записал сообщение'
                                        f'\n\n\rВаше сообщение для рассылки отправил ниже.'
                                        f'\n\n\rЕсли все правильно нажмите 💀Рассылка юзерам из ЧС, если нет - ❌Отменить',reply_markup=send_black_key())
        await bot.copy_message(user_id, user_id, message_id=id_mes)
    elif users_black==None:

        await bot.send_message(user_id, f'✅Записал сообщение'
                                        f'\n\n\rВаше сообщение для рассылки отправил ниже.'
                                        f'\n\n\rЕсли все правильно нажмите ✅Начать рассылку, если нет - ❌Отменить',reply_markup=send_key())
        await bot.copy_message(user_id, user_id, message_id=id_mes)

    await call.answer()

@router.callback_query(F.data.in_(['cancel_send_reg','cancel_sending','cancel_edit']))
async def get_cancel_sending(call: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_message(call.from_user.id, f'❌Отменил изменения!')
    await state.clear()
    await call.answer()

@router.callback_query(F.data.in_(
    ['start_sending_all', 'start_sending_only_reg', 'start_sending_noreg', 'start_sending_chs']))
async def start_sending_reg(call: CallbackQuery, bot: Bot, state: FSMContext):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    adm_id = call.message.chat.id
    data = await state.get_data()
    mess_id = data.get('id')
    text_button = data.get('text_button')
    url = data.get('url')
    sended = 0
    not_send = 0
    user_list = []
    if call.data=='start_sending_all':
        cursor.execute("SELECT user_id FROM users")
        user_list_tuples = cursor.fetchall()
        user_list = [user_id[0] for user_id in user_list_tuples]
    elif call.data=='start_sending_only_reg':
        cursor.execute("SELECT user_id FROM users WHERE platform_id!=0")
        user_list_tuples = cursor.fetchall()
        user_list = [user_id[0] for user_id in user_list_tuples]
    elif call.data=='start_sending_noreg':
        cursor.execute("SELECT user_id FROM users WHERE platform_id==0")
        user_list_tuples = cursor.fetchall()
        user_list = [user_id[0] for user_id in user_list_tuples]
    elif call.data=='start_sending_chs':
        user_list = data.get('black_list')
    for user_id in user_list:
        if text_button and url:
            try:
                await bot.copy_message(user_id,adm_id, message_id=mess_id, parse_mode='HTML', reply_markup=coonstruct_key(text_button,url))
                sended += 1
                await asyncio.sleep(.05)
            except Exception as e:
                print(f"Error while sending message to user {user_id}: {e}")
                not_send += 1
        else:
            try:
                await bot.copy_message(user_id,adm_id, message_id=mess_id, parse_mode='HTML' )
                sended += 1
                await asyncio.sleep(.05)
            except Exception as e:
                print(f"Error while sending message to user {user_id}: {e}")
                not_send += 1
    await bot.send_message(adm_id,f"Рассылка завершена! Отправлено {sended}, не отправлено {not_send}")
    await state.clear()
    await call.answer()
    conn.commit()
    cursor.close()

@router.callback_query(F.data.in_(['on_sub', 'off_sub']))
async def update_sub(call: CallbackQuery,bot: Bot):
    adm_id = config.admin_id
    user_id = call.from_user.id
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    if call.data=='on_sub':
        cursor.execute('UPDATE creator SET check_sub = 1 WHERE user_id = ?', (adm_id,))
        await bot.send_message(user_id, f'✅Включил проверку подписки на канал!')
    elif call.data=='off_sub':
        cursor.execute('UPDATE creator SET check_sub = 0 WHERE user_id = ?', (adm_id,))
        await bot.send_message(user_id, f'❌Выключил проверку подписки на канал!')
    await call.answer()
    conn.commit()
    cursor.close()


def buttons_sett_key(statuses: dict):
    key_build = InlineKeyboardBuilder()

    button_labels = {
        "is_button_free": "Кнопка бесплатного получения",
        "help": "Кнопка Помощь",
        "reviews": "Кнопка Отзывы",
        "crypto_bot": "Crypto Bot",
        "crystal_pay": "Crystal Pay",
        "ammer_pay": "Ammer Pay",
        "cis_pay": "Cis Pay",
    }

    for key, label in button_labels.items():
        emoji = '🟢' if statuses[key] else '🔴'
        action = f'off_{key}' if statuses[key] else f'on_{key}'
        key_build.button(text=f"{emoji} {label}", callback_data=action)

    key_build.button(text="Ссылка Помощь", callback_data="edit_help_link")
    key_build.button(text="Ссылка отзывы", callback_data="edit_rew_link")
    key_build.button(text="Текст кнопки бесплатного получения🇷🇺", callback_data="edit_get_free_text")
    key_build.button(text="Текст кнопки бесплатного получения🇺🇸", callback_data="edit_get_free_text_us")

    key_build.adjust(1,2, 2,2, 1, 1, 1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard=False)


@router.callback_query(F.data=='buttons_turn_on_off')
async def buttons_settings(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    msg = "⚙️ <b>Настройки включения и выключения кнопок</b>"

    query = "SELECT crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay, reviews, help,is_button_free FROM creator WHERE user_id = ?"
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)

    if not data:
        return await call.answer("Данные не найдены", show_alert=True)

    crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay, reviews, help,is_button_free = data[0]

    statuses = {
        "is_button_free":bool(is_button_free),
        "crypto_bot": bool(crypto_bot),
        "crystal_pay": bool(crystal_pay),
        "ammer_pay":bool(ammer_pay),
        "cis_pay":bool(cis_pay),
        "reviews": bool(reviews),
        "help": bool(help)
    }



    await bot.send_message(
        user_id,
        msg,
        reply_markup=buttons_sett_key(statuses)
    )
    await call.answer()

@router.callback_query(F.data.startswith('off_') | F.data.startswith('on_'))
async def turn_on_off_buttons(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    action, button_name = call.data.split("_", 1)

    new_status = 1 if action == "on" else 0
    query = f"UPDATE creator SET {button_name} = ? WHERE user_id = ?"
    params = (new_status, config.admin_id)
    await execute_query(query, params, commit=True)

    # Получаем обновленные данные
    query = "SELECT crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay, reviews, help,is_button_free FROM creator WHERE user_id = ?"
    params = (config.admin_id,)
    data = await execute_query(query, params, False, 2)

    if not data:
        return await call.answer("Ошибка при обновлении", show_alert=True)

    crypto_bot, smart_glocal, crystal_pay,ammer_pay, cis_pay, reviews, help,is_button_free = data[0]

    statuses = {
        "is_button_free":bool(is_button_free),
        "crypto_bot": bool(crypto_bot),
        "crystal_pay": bool(crystal_pay),
        "ammer_pay":bool(ammer_pay),
        "cis_pay":bool(cis_pay),
        "reviews": bool(reviews),
        "help": bool(help)
    }

    await call.message.edit_reply_markup(reply_markup=buttons_sett_key(statuses))
    await call.answer("Статус кнопки обновлён!")


@router.callback_query(F.data.startswith('edit_get_free_text'))
async def edit_text_free_btn(call:CallbackQuery,bot:Bot,state:FSMContext):
    if call.data=='edit_get_free_text_us':
        msg = f'🇺🇸Отправьте сообщение, которое будет получать пользователь при переходе в раздел "Получить бота бесплатно".'
    else:
        msg = f'🇷🇺Отправьте сообщение, которое будет получать пользователь при переходе в раздел "Получить бота бесплатно".'
    await bot.send_message(call.from_user.id, msg, reply_markup=cancel_admin_key())
    await call.answer()
    await state.set_state(StepsForm.wait_free_text_btn)
    await state.update_data(call_data = call.data)


@router.message(StepsForm.wait_free_text_btn)
async def save_free_text_btn(message:Message,state:FSMContext):
    mes_id = message.message_id
    await state.update_data(free_mes_id = mes_id)
    await message.answer(f'✅Записал сообщение, вы хотите добавить кнопку к этому сообщению?', reply_markup=add_btn_free_key())


@router.callback_query(F.data=='no_btn_free_mess')
async def no_btn_free_msg(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    data = await state.get_data()
    free_mes_id = data.get('free_mes_id')
    str_mes_id = f'{free_mes_id}~0~0'
    call_data = data.get('call_data')
    if call_data=='edit_get_free_text':
        query = 'UPDATE creator SET mes_id_free = ?, admin_id_free = ? WHERE user_id = ?'
    else:
        query = 'UPDATE creator SET mes_id_free_en = ?, admin_id_free = ? WHERE user_id = ?'
    params = (str_mes_id, user_id, config.admin_id)
    await execute_query(query, params, True, 0)
    await bot.edit_message_text( text=f'✅Успешно записал сообщение!', chat_id=user_id, message_id=call.message.message_id)
    await state.clear()

@router.callback_query(F.data=='add_btn_free_mess')
async def write_btn_free_msg(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    msg = f'✏️Отправьте текст кнопки.'
    await bot.edit_message_text(msg, chat_id=user_id, message_id=call.message.message_id, reply_markup=cancel_admin_key())
    await state.set_state(StepsForm.wait_btn_name_msg_free)

@router.message(StepsForm.wait_btn_name_msg_free)
async def save_btn_name_free(message:Message,bot:Bot,state:FSMContext):
    name_btn_free = message.text
    msg = (f'Записал название кнопки.'
           f'\n✏️Отправьте ссылку для кнопки.')
    await message.answer(msg, reply_markup=cancel_admin_key())
    await state.set_state(StepsForm.wait_btn_link_msg_free)
    await state.update_data(name_btn_free = name_btn_free)

@router.message(StepsForm.wait_btn_link_msg_free)
async def show_free_msg(message:Message,bot:Bot,state:FSMContext):
    user_id = message.from_user.id
    link_btn_free = message.text
    msg = (f'✅Записал сообщение. Отправил его ниже.')
    data = await state.get_data()
    name_btn_free = data.get('name_btn_free')
    free_mes_id = data.get('free_mes_id')
    await bot.send_message(user_id, msg)
    await bot.copy_message(chat_id=user_id, from_chat_id=user_id, message_id=free_mes_id, reply_markup=coonstruct_key(name_btn_free, link_btn_free))
    mes_id_free = f'{free_mes_id}~{name_btn_free}~{link_btn_free}'
    call_data = data.get('call_data')
    if call_data=='edit_get_free_text':
        query = 'UPDATE creator SET mes_id_free = ?, admin_id_free = ? WHERE user_id = ?'
    else:
        query = 'UPDATE creator SET mes_id_free_en = ?, admin_id_free = ? WHERE user_id = ?'
    params = (mes_id_free,user_id, config.admin_id)
    await execute_query(query,params,True,0)
    await state.clear()

@router.callback_query(F.data=='edit_rew_link')
async def edit_link_rev(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    data = await execute_query('SELECT link_reviews FROM creator WHERE user_id = ?', (config.admin_id,), False, 1)
    link_reviews = data[0]
    msg = (f'Текущая ссылка на Отзывы - {link_reviews}'
           f'\nОтправьте новую ссылку для кнопки "Отзывы"⬇️')
    await bot.send_message(user_id,msg, disable_web_page_preview=True, reply_markup=cancel_admin_key())
    await state.set_state(StepsForm.wait_link_rew)
    await call.answer()

@router.message(StepsForm.wait_link_rew)
async def save_link_rew(message:Message,bot:Bot,state:FSMContext):
    rew_link = message.text
    query = 'UPDATE creator SET link_reviews = ? WHERE user_id = ?'
    params = (rew_link, config.admin_id)
    await execute_query(query, params, True, 0)
    await message.answer(f'✅Ссылку успешно записал!')
    await state.clear()


@router.callback_query(F.data=='edit_help_link')
async def edit_link_help(call:CallbackQuery,bot:Bot,state:FSMContext):
    user_id = call.from_user.id
    data = await execute_query('SELECT link_help FROM creator WHERE user_id = ?', (config.admin_id,), False, 1)
    link_reviews = data[0]
    msg = (f'Текущая ссылка на Помощь - {link_reviews}'
           f'\nОтправьте новую ссылку для кнопки "Помощь"⬇️')
    await bot.send_message(user_id,msg, disable_web_page_preview=True, reply_markup=cancel_admin_key())
    await state.set_state(StepsForm.wait_link_help)
    await call.answer()

@router.message(StepsForm.wait_link_help)
async def save_link_rew(message:Message,bot:Bot,state:FSMContext):
    rew_link = message.text
    query = 'UPDATE creator SET link_help = ? WHERE user_id = ?'
    params = (rew_link, config.admin_id)
    await execute_query(query, params, True, 0)
    await message.answer(f'✅Ссылку успешно записал!')
    await state.clear()



async def execute_query(query: str, params: tuple = (), commit: bool = True, one: int = 0):
    async with aiosqlite.connect('users.db') as conn:
        async with conn.execute(query, params) as cursor:
            if commit:
                await conn.commit()  # Подтверждаем изменения только при необходимости
            if one == 1:
                return await cursor.fetchone()
            elif one == 2:
                return await cursor.fetchall()
            else:
                pass



async def timer_day(bot:Bot,sleep:int, user_id:int, lang:str):
    await asyncio.sleep(sleep)
    query = 'UPDATE users SET date_start_sub = ?,date_end_sub = ?, sub_name = ? WHERE user_id = ?'
    params = ('0','0',2,user_id)
    await execute_query(query, params, True, 0)
    if lang=='ru': msg = f'🔔<b>Ваша подписка завершена!</b>\n🔥Вы можете продлить подписку в главном меню или получить доступ в бота бесплатно.'
    else:msg = f'🔔 </b>Your subscription has ended!</b>\n🔥You can renew your subscription in the main menu or get access to the bot for free.'
    await bot.send_message(chat_id=user_id, text=msg)



async def update_subscribe(bot:Bot):
    query = '''SELECT user_id, date_start_sub, date_end_sub, sub_name 
               FROM users 
               WHERE date_start_sub != '0' 
               AND date_start_sub IS NOT NULL'''
    params = ()
    data = await execute_query(query, params, False, 2)

    users_list = [f"{user_id}${date_start_sub}${date_end_sub}${sub_name}"
                  for user_id, date_start_sub, date_end_sub, sub_name in data]

    now = datetime.datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    for user in users_list:
        user_id = user.split('$')[0]
        date_start_sub = user.split('$')[1]
        date_end_sub = user.split('$')[2]
        sub_name = user.split('$')[3]

        try:
            member = await bot.get_chat_member(chat_id=user_id, user_id=int(user_id))
            lang = member.user.language_code
            if lang not in ['ru','en']:
                lang = 'en'

            # Преобразуем даты в datetime объекты
            end_date = datetime.datetime.strptime(date_end_sub, "%Y-%m-%d %H:%M:%S")
            time_remaining = end_date - now

            # Если подписка уже истекла
            if time_remaining.total_seconds() <= 0:
                await timer_day(bot, 0, int(user_id), lang)  # Завершаем сразу
                continue

            # Если осталось менее 7 дней (604800 секунд)
            if time_remaining.total_seconds() < 604800 and time_remaining.total_seconds() > 86400:
                # Отправляем предупреждение о скором окончании
                if lang == 'ru':
                    msg = f"🔔<b>Ваша подписка заканчивается через {time_remaining.days} дней!</b>\n🔥Вы можете продлить подписку в любой момент в главном меню."
                else:
                    msg = f"🔔<b>Your subscription expires in {time_remaining.days} days!</b>\n🔥You can renew your subscription anytime in the main menu."
                await bot.send_message(user_id, msg)

                # Устанавливаем таймер на точное время окончания
                # sleep = time_remaining.total_seconds()
                # asyncio.create_task(timer_day(bot, sleep, int(user_id), lang))

            # Если осталось менее 24 часов (86400 секунд)
            elif time_remaining.total_seconds() <= 86400:
                # hours_remaining = int(time_remaining.total_seconds() // 3600)
                # if lang == 'ru':
                #     msg = f"⏳ Ваша подписка заканчивается через {hours_remaining} часов!"
                # else:
                #     msg = f"⏳ Your subscription expires in {hours_remaining} hours!"
                # await bot.send_message(user_id, msg)

                sleep = time_remaining.total_seconds()
                asyncio.create_task(timer_day(bot, int(sleep), int(user_id), str(lang)))

        except Exception as e:
            print(f"Error processing user {user_id}: {e}")