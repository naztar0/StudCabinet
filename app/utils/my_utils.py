import json
import requests
from contextlib import suppress
from aiogram import types
from aiogram.utils import exceptions, callback_data
from app import misc
from app.bot import __
from app.utils.database_connection import DatabaseConnection


class ResTypes:
    MAIL = 0x00
    PASS = 0x01
    STUD_ID = 0x02
    LANG = 0x03
    GROUP_ID = 0x04
    FACULTY = 0x05


class Keyboards:
    UA_1 = 0x00
    UA_2 = 0x01
    RU_1 = 0x02
    RU_2 = 0x03


class CallbackFuncs:
    PAGE_1 = 0x00
    PAGE_2 = 0x01
    PAGE_3 = 0x02
    PAGE_4 = 0x03
    PAGE_5 = 0x04
    SCHEDULE = 0x05
    SPORT_TYPE = 0x06
    SPORT_DAY = 0x07
    RATING_SHOW_ALL = 0x08
    RATING_SHOW_ALL_SORT = 0x09
    HISTOGRAM_2 = 0x0a
    HISTOGRAM_4 = 0x0b


async def delete_message(func, **kwargs):
    with suppress(exceptions.MessageCantBeDeleted,
                  exceptions.MessageToDeleteNotFound):
        await func(**kwargs)


async def send_message(func, **kwargs):
    with suppress(exceptions.BotBlocked,
                  exceptions.UserDeactivated,
                  exceptions.ChatNotFound,
                  exceptions.BadRequest):
        return await func(**kwargs)


def req_post(url, method='POST'):
    try:
        if method == 'POST':
            response = requests.post(url, timeout=20)
        elif method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            return
    except (requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError): return
    return response


def esc_markdown(s):
    if not s: return ''
    return s.replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[')


def reply_keyboard(key_type: int):
    buttons = None
    if key_type == Keyboards.UA_1:
        buttons = misc.buttons_ua_1
    elif key_type == Keyboards.UA_2:
        buttons = misc.buttons_ua_2
    elif key_type == Keyboards.RU_1:
        buttons = misc.buttons_ru_1
    elif key_type == Keyboards.RU_2:
        buttons = misc.buttons_ru_2
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, input_field_placeholder="Select a button...")
    for btn in buttons:
        key.insert(btn)
    return key


def set_callback(func, data):
    return callback_data.CallbackData('@', 'func', 'json', sep='&').new(func, json.dumps(data, separators=(',', ':')))


def get_callback(data):
    try:
        cd = callback_data.CallbackData('@', 'func', 'json', sep='&').parse(data)
    except ValueError:
        return
    parsed = cd.get('json')
    func = cd.get('func')
    if parsed is None or func is None or not func.isdigit():
        return
    return int(func), json.loads(parsed)


def generate_inline_keyboard(page, count, row=3):
    key = types.InlineKeyboardMarkup(row_width=row)
    for i in range(1, count + 1):
        key.insert(types.InlineKeyboardButton(text=str(i), callback_data=set_callback(page, i)))
    return key


async def api_request(message=None, path=misc.api_cab, **kwargs):
    args = ''
    for arg in kwargs:
        args += f'&{arg.replace("passwd", "pass", 1)}={kwargs[arg]}'
    args = '?' + args[1:]
    response = req_post(misc.api_url + path + args)
    if not response:
        if message:
            await message.answer(misc.req_err_msg)
        return
    return response.json()


async def reg_key(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
    key.add(misc.sign_in_butt, misc.buttons_ua_2[4])
    await message.answer("Щоб продовжити натисніть на одну з кнопок", reply_markup=key)


async def authentication(message, first=False, skip=False):
    findQuery = "SELECT mail, pass, stud_id, lang, group_id, faculty FROM users WHERE user_id=(%s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(findQuery, [message.chat.id])
        auth = cursor.fetchone()
    if skip:
        return auth
    if first:
        if auth:
            key_type = Keyboards.UA_1
            if auth[ResTypes.LANG] == 'ru':
                key_type = Keyboards.RU_1
            await message.answer(__('auth_err_1', locale=auth[ResTypes.LANG]), reply_markup=reply_keyboard(key_type))
    else:
        if not auth:
            await message.answer(misc.auth_err_msg)
            await reg_key(message)
    return auth


__all__ = ('ResTypes', 'Keyboards', 'CallbackFuncs', 'delete_message', 'send_message', 'req_post', 'esc_markdown', 'reply_keyboard',
           'set_callback', 'get_callback', 'generate_inline_keyboard', 'api_request', 'authentication', 'reg_key')
