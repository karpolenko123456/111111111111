from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder, WebAppInfo
from  aiogram.fsm.state import StatesGroup, State
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram import Bot

import config


class StepsForm(StatesGroup):
    wait_id = State()
    wait_ref_link = State()
    wait_mes_for_send = State()
    wait_url_button = State()
    wait_text_button = State()
    wait_promo = State()
    wait_mes_auto = State()
    wait_text_button_a = State()
    wait_url_button_a = State()
    wait_mes_for_send_a = State()
    wait_ref_link_tr = State()
    wait_promo_tr = State()
    wait_link_sub = State()
    wait_forward_mes = State()
    wait_id_admin = State()
    wait_id_black = State()
    wait_link_rew = State()
    wait_ammer_pay = State()
    wait_free_text_btn = State()
    wait_btn_name_msg_free = State()
    wait_btn_link_msg_free = State()
    wait_user_acces = State()
    wait_link_help = State()

async def set_comands(bot:Bot):
    commands = [
        BotCommand(
            command='start',
            description='Запуск бота'
        )
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

def coonstruct_key(text, url):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{text}', url=f'{url}')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def subscr_key(url,btn1,btn2):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{btn1}✅', callback_data='chek_sub')
    key_build.button(text=f'{btn2}📎', url=url)
    key_build.adjust(2)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def start_key(name):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{name}🚀', callback_data='activate')
    key_build.adjust(2)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def next_key(name):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{name}🚀', callback_data='activate_second')
    key_build.adjust(2)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def tarifs_key(free, month, six, year, fre_ref, is_rewievs,reviews,url_reviews,is_help, help,url_help, is_btn_free):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'📈{month}', callback_data='month_99')
    key_build.button(text=f'💎{six}', callback_data='six_499')
    key_build.button(text=f'👑{year}', callback_data='year_799')
    key_build.button(text=f'🚀{free}', callback_data='get_bot_free_day')
    if is_btn_free==1:
        key_build.button(text=f'🔥{fre_ref}', callback_data=f'get_free_bot_btn')
    if int(is_rewievs)==1:
        key_build.button(text=f'ℹ️{reviews}', url=f'{url_reviews}')
    if int(is_help)==1:
        key_build.button(text=f'⭐️{help}', url=f'{url_help}')
    key_build.adjust(1,1,1,1,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def method_keys(is_crystal, is_bot, is_cis,is_ammer,is_smart):
    key_build = InlineKeyboardBuilder()
    if is_crystal==1:
        key_build.button(text=f'Crystal Pay (crypto + cards💳)', callback_data='crystal_pay_start')
    if is_bot:
        key_build.button(text=f'CryptoBot (crypto)', callback_data='cryptobot_pay_start')
    if is_cis==1:
        key_build.button(text=f'Cis Pay (crypto + cards💳)', callback_data='cis_pay_start')
    if is_ammer==1:
        key_build.button(text=f'Ammer Pay (cards💳)', callback_data='ammer_pay_start')


    key_build.button(text=f'🔙', callback_data='back_active')
    key_build.adjust(1,1,1,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)


def method_keys_menu(is_crystal, is_bot, is_cis,is_ammer,is_smart):
    key_build = InlineKeyboardBuilder()
    if is_crystal==1:
        key_build.button(text=f'Crystal Pay (crypto + cards💳)', callback_data='crystal_pay')
    if is_bot:
        key_build.button(text=f'CryptoBot (crypto)', callback_data='cryptobot_pay')
    if is_cis==1:
        key_build.button(text=f'Cis Pay (crypto + cards💳)', callback_data='cis_pay')
    if is_ammer==1:
        key_build.button(text=f'Ammer Pay (cards💳)', callback_data='ammer_pay')


    key_build.button(text=f'🔙', callback_data='profile')
    key_build.adjust(1,1,1,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def reg_key(url):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'Регистрация✅', url=url)
    key_build.button(text=f'Проверить регистрацию🔍', callback_data='check_register')
    key_build.adjust(1,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def deposit_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'Проверить депозит🔍', callback_data='check_deposit')
    key_build.adjust(2)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def main_keyboard(signals,profile,is_free, get_free, is_rewievs,reviews,url_reviews,is_help, help,url_help,is_btn_free):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{signals}', callback_data='signals')
    key_build.button(text=f'{profile}', callback_data='profile')
    if int(is_free)==0 and int(is_btn_free)==1:
        key_build.button(text=f'{get_free}', callback_data=f'get_free_bot_btn')
    if int(is_rewievs)==1:
        key_build.button(text=f'ℹ️{reviews}', url=f'{url_reviews}')
    if int(is_help)==1:
        key_build.button(text=f'⭐️{help}', url=f'{url_help}')
    key_build.adjust(1,1,1,2)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def profile_key(month,six,year):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'📈{month}', callback_data='paymonth_99')
    key_build.button(text=f'💎{six}', callback_data='paysix_499')
    key_build.button(text=f'👑{year}', callback_data='payyear_799')
    key_build.button(text=f'🔙', callback_data='back_main')
    key_build.adjust(1,2,1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def signals_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'BTCUSDT', callback_data='BTCUSDT')
    key_build.button(text=f'ETHUSDT', callback_data='ETHUSDT')
    key_build.button(text=f'SOLUSDT', callback_data='SOLUSDT')
    key_build.button(text=f'100PEPEUSDT', callback_data='PEPEUSDT')
    key_build.button(text=f'WIFUSDT', callback_data='WIFUSDT')
    key_build.button(text=f'APTUSDT', callback_data='APTUSDT')
    key_build.button(text=f'XRPUSDT', callback_data='XRPUSDT')
    key_build.button(text=f'100SHIBUSDT', callback_data='SHIBUSDT')
    key_build.button(text=f'DOGEUSDT', callback_data='DOGEUSDT')
    key_build.button(text=f'100BONKUSDT', callback_data='BONKUSDT')
    key_build.button(text=f'TIAUSDT', callback_data='TIAUSDT')
    key_build.button(text=f'BNBUSDT', callback_data='BNBUSDT')
    key_build.button(text=f'SEIUSDT', callback_data='SEIUSDT')
    key_build.button(text=f'WLDUSDT', callback_data='WLDUSDT')
    key_build.button(text=f'ORDIUSDT', callback_data='ORDIUSDT')
    key_build.button(text=f'AVAXUSDT', callback_data='AVAXUSDT')
    key_build.button(text=f'NEARUSDT', callback_data='NEARUSDT')
    key_build.button(text=f'ADAUSDT', callback_data='ADAUSDT')
    key_build.button(text=f'DOTUSDT', callback_data='DOTUSDT')
    key_build.button(text=f'UNFIUSDT', callback_data='UNFIUSDT')
    key_build.button(text=f'ATOMUSDT', callback_data='ATOMUSDT')
    key_build.button(text=f'XLMUSDT', callback_data='XLMUSDT')
    key_build.button(text=f'ZECUSDT', callback_data='ZECUSDT')
    key_build.button(text=f'100LUNCUSDT', callback_data='LUNCUSDT')

    key_build.button(text=f'TON', callback_data='TONUSDT')
    key_build.button(text=f'LINK', callback_data='LINKUSDT')
    key_build.button(text=f'LTC', callback_data='LTCUSDT')

    key_build.button(text=f'DIA', callback_data='DIAUSDT')
    key_build.button(text=f'TRUMP', callback_data='TRUMPUSDT')
    key_build.button(text=f'VET VeChain', callback_data='VETUSDT')

    key_build.button(text=f'ALGO Algorand', callback_data='ALGOUSDT')
    key_build.button(text=f'ARB Arbitrum', callback_data='ARBUSDT')
    key_build.button(text=f'EOS', callback_data='EOSUSDT')

    key_build.button(text=f'🔙', callback_data='back_main')
    key_build.adjust(3,3,3,3,3,3,3,3)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)


def get_signal_key(name):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{name}📊', callback_data='get_new_signal')
    key_build.adjust(2)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)



def bot_pay_key(name,url,is_menu):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{name}💰', url=url)
    if is_menu==1:
        key_build.button(text=f'🔙', callback_data='back_main')
    else:
        key_build.button(text=f'🔙', callback_data='back_active')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def cancel_pay_back_key(name,is_menu):
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'{name}', pay=True)

    if is_menu==1:
        key_build.button(text=f'🔙', callback_data='back_main')
    else:
        key_build.button(text=f'🔙', callback_data='back_active')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)

def back_fter_pay_key():
    key_build = InlineKeyboardBuilder()
    key_build.button(text=f'🔙', callback_data='back_main')
    key_build.adjust(1)
    return key_build.as_markup(resize_keyboard=True, one_time_keyboard = False)