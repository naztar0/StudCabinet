import json
import requests
from random import choice
from contextlib import suppress
from aiogram import types
from aiogram.utils import exceptions, callback_data
from app import misc
from app.misc import i18n, __
from app.utils.database_connection import DatabaseConnection


class Student:
    def __init__(self, args):
        if not args or not isinstance(args, (list, tuple, dict)) or len(args) < 6:
            args = tuple(None for _ in range(6))
        self.mail = args[0]
        self.password = args[1]
        self.id = args[2]
        self.lang = args[3] or i18n.default
        self.group_id = args[4]
        self.faculty = args[5]

    def __bool__(self):
        return all((self.mail, self.password, self.id, self.lang, self.group_id, self.faculty))

    def text(self, name):
        return __(name, locale=self.lang)


class Keyboards:
    UA_1 = 0x00
    UA_2 = 0x01
    RU_1 = 0x02
    RU_2 = 0x03
    EN_1 = 0x04
    EN_2 = 0x05


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


def esc_md(s):
    if s is None:
        return ''
    if isinstance(s, str):
        if not s: return ''
        return s.replace('_', '\\_').replace('*', '\\*').replace('`', "'").replace('[', '\\[')
    if isinstance(s, dict):
        return {key: esc_md(x) for key, x in s.items()}
    if isinstance(s, list):
        return list(map(lambda x: esc_md(x), s))
    if isinstance(s, (int, float, bool)):
        return str(s)


def get_update_json(filename, key=None, value=None):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not key:
        return data
    if not value:
        return data.get(key)
    data[key] = value
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


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
    elif key_type == Keyboards.EN_1:
        buttons = misc.buttons_en_1
    elif key_type == Keyboards.EN_2:
        buttons = misc.buttons_en_2
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, input_field_placeholder=choice(misc.placeholders))
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
    student = Student(auth)
    if skip:
        return student
    if first:
        if student:
            key_type = Keyboards.UA_1
            if student.lang == 'ru':
                key_type = Keyboards.RU_1
            elif student.lang == 'en':
                key_type = Keyboards.EN_1
            await message.answer(student.text('auth_err_1'), reply_markup=reply_keyboard(key_type))
    else:
        if not student:
            await message.answer(misc.auth_err_msg)
            await reg_key(message)
    return student


def auth_student(function):
    async def decorator(message, *args, **kwargs):
        kwargs['student'] = await authentication(message)
        if not kwargs['student']:
            return
        if function.__name__ == 'decorator':
            expected = kwargs
        else:
            expected = {key: kwargs[key] for key in function.__code__.co_varnames if kwargs.get(key)}
        return await function(message, *args, **expected)
    return decorator


def load_page(**kwargs):
    def wrapper(function):
        async def decorator(message, **kwargs_):
            api_kwargs = {}
            student: Student = kwargs_.get('student')
            if student:
                api_kwargs['email'] = student.mail
                api_kwargs['passwd'] = student.password
            api_kwargs['semestr'] = kwargs_.get('sem') or ''
            api_kwargs['day'] = kwargs_.get('day') or ''
            api_kwargs['sport_id'] = kwargs_.get('sport_id') or ''
            data = await api_request(message, **api_kwargs, **kwargs)
            if not data and not kwargs.get('allow_invalid'):
                if student:
                    await message.answer(student.text('not_found'))
                return
            kwargs_['api_data'] = data
            expected = {key: kwargs_[key] for key in function.__code__.co_varnames if kwargs_.get(key)}
            return await function(message, **expected)
        return decorator
    return wrapper


__all__ = ('Keyboards', 'CallbackFuncs', 'delete_message', 'send_message', 'req_post', 'esc_md', 'reply_keyboard', 'set_callback', 'get_callback',
           'generate_inline_keyboard', 'api_request', 'authentication', 'reg_key', 'Student', 'auth_student', 'load_page', 'get_update_json')
