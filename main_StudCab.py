#!/usr/bin/env python
import json
from asyncio import sleep
import constants as c
import my_utils as mu
from settings import DEBUG
import histogram
from database_connection import DatabaseConnection
import record_book

from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage


bot = Bot(c.token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup): authorization = State()
class Feedback(StatesGroup): text = State()
class SendMessageToUsers(StatesGroup): text = State()


sign_in_butt = "👥 Увійти в кабінет"
buttons_ru_1 = ["ℹ Общая информация", "📕 Зачётная книжка", "📊 Рейтинг", "⚠ Долги", "📆 Расписание занятий", "📆 Расписание спорт. каф.", "🗓 Учебный план", "➡ Другое"]
buttons_ua_1 = ["ℹ Загальна інформація", "📕 Залікова книжка", "📊 Рейтинг", "⚠ Борги", "📆 Розклад занять", "📆 Розклад спорт. каф.", "🗓 Навчальний план", "➡ Інше"]
buttons_ru_2 = ["💳 Оплаты за обучение", "📄 Семестровый план", "❓Помощь", "🇷🇺 Язык", "⬅  Назад"]
buttons_ua_2 = ["💳 Оплати за навчання", "📄 Семестровий план", "❓Підтримка", "🇺🇦 Мова", "⬅ Назад"]
req_err_msg = "😔 Не вдалося виконати запит, спробуйте пізніше"


def keyboard_ru_1():
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_1 = types.KeyboardButton(buttons_ru_1[0])
    but_2 = types.KeyboardButton(buttons_ru_1[1])
    but_3 = types.KeyboardButton(buttons_ru_1[2])
    but_4 = types.KeyboardButton(buttons_ru_1[3])
    but_5 = types.KeyboardButton(buttons_ru_1[4])
    but_6 = types.KeyboardButton(buttons_ru_1[5])
    but_7 = types.KeyboardButton(buttons_ru_1[6])
    but_8 = types.KeyboardButton(buttons_ru_1[7])
    key.add(but_1, but_2)
    key.add(but_3, but_4)
    key.add(but_5, but_6)
    key.add(but_7, but_8)
    return key


def keyboard_ua_1():
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_1 = types.KeyboardButton(buttons_ua_1[0])
    but_2 = types.KeyboardButton(buttons_ua_1[1])
    but_3 = types.KeyboardButton(buttons_ua_1[2])
    but_4 = types.KeyboardButton(buttons_ua_1[3])
    but_5 = types.KeyboardButton(buttons_ua_1[4])
    but_6 = types.KeyboardButton(buttons_ua_1[5])
    but_7 = types.KeyboardButton(buttons_ua_1[6])
    but_8 = types.KeyboardButton(buttons_ua_1[7])
    key.add(but_1, but_2)
    key.add(but_3, but_4)
    key.add(but_5, but_6)
    key.add(but_7, but_8)
    return key


def keyboard_ru_2():
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_1 = types.KeyboardButton(buttons_ru_2[0])
    but_2 = types.KeyboardButton(buttons_ru_2[1])
    but_3 = types.KeyboardButton(buttons_ru_2[2])
    but_4 = types.KeyboardButton(buttons_ru_2[3])
    but_5 = types.KeyboardButton(buttons_ru_2[4])
    key.add(but_1, but_2)
    key.add(but_3, but_4)
    key.add(but_5)
    return key


def keyboard_ua_2():
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_1 = types.KeyboardButton(buttons_ua_2[0])
    but_2 = types.KeyboardButton(buttons_ua_2[1])
    but_3 = types.KeyboardButton(buttons_ua_2[2])
    but_4 = types.KeyboardButton(buttons_ua_2[3])
    but_5 = types.KeyboardButton(buttons_ua_2[4])
    key.add(but_1, but_2)
    key.add(but_3, but_4)
    key.add(but_5)
    return key


@dp.message_handler(commands=['start'])
async def handle_text(message: types.Message):
    await reg_key(message)


async def reg_key(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    but_1 = types.KeyboardButton(sign_in_butt)
    but_2 = types.KeyboardButton(buttons_ua_2[2])
    key.add(but_1)
    key.add(but_2)
    await message.answer("Щоб продовжити натисніть на одну з кнопок", reply_markup=key)


@dp.message_handler(commands=['feedback'])
async def handle_text(message: types.Message):
    auth = await authentication(message, skip=True)
    lang = auth[3] if auth else 'ua'
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    await message.reply(strings[lang]['feedback_start'])
    await Feedback.text.set()


@dp.message_handler(content_types=[types.ContentType.ANY], state=Feedback.text)
async def feedback(message: types.Message, state: FSMContext):
    await state.finish()

    auth = await authentication(message, skip=True)
    lang = auth[3] if auth else 'ua'
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)

    if message.text:
        for exception in ['/exit', sign_in_butt], buttons_ua_1, buttons_ru_1:
            if message.text in exception:
                await message.reply(strings[lang]['cancel'])
                return
    text = f"*Feedback!\n\nUser:* [{message.from_user.full_name}](tg://user?id={message.from_user.id})\n" \
           f"*UserName:* @{message.from_user.username}\n*ID:* {message.from_user.id}"
    await bot.send_message(c.admin, text, parse_mode="Markdown")
    await bot.forward_message(c.admin, message.chat.id, message.message_id)
    await message.answer(strings[lang]['feedback_finish'])


@dp.message_handler(commands=['send'])
async def handle_text(message: types.Message):
    if message.chat.id == c.admin:
        await message.answer("Введите сообщение для отправки пользователям (Markdown)\n\nОтмена - [/exit]")
        await SendMessageToUsers.text.set()


@dp.message_handler(content_types=['text'], state=SendMessageToUsers.text)
async def handle_text(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == "/exit":
        await message.answer("Отменено")
        return
    try:
        test = await message.answer(message.text, parse_mode='Markdown')
    except utils.exceptions.CantParseEntities:
        await message.answer("Неверный формат Markdown!")
        return
    await bot.delete_message(message.chat.id, test.message_id)
    selectQuery = "SELECT user_id FROM users"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(selectQuery)
        users = cursor.fetchall()
    i = 0
    j = 0
    blocked = []
    for user in users:
        if await mu.send_message(bot.send_message, utils, chat_id=user[0], text=message.text, parse_mode='Markdown'):
            i += 1
        else:
            j += 1
            blocked.append(str(user[0]))
        await sleep(.05)
    blocked = '\n'.join(blocked)
    await message.answer(f"Отправлено: {i}\nНе отправлено: {j}\n\n{blocked}")


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    if message.text == sign_in_butt:
        auth = await authentication(message, first=True)
        if auth:
            return
        await message.answer("*Введіть email і пароль від особистого кабінету*\n\nНаприклад:\ndemo@gmail.com d2v8F3", parse_mode="Markdown")
        await Form.authorization.set()
    elif message.text == buttons_ua_2[2]:
        await message.answer(c.helper_ua, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == buttons_ru_2[2]:
        await message.answer(c.helper_ru, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == buttons_ua_1[0] or message.text == buttons_ru_1[0]:
        await page_1(message)
    elif message.text == buttons_ua_1[1] or message.text == buttons_ru_1[1]:
        key = types.InlineKeyboardMarkup()
        a1 = types.InlineKeyboardButton(text="1", callback_data="21")
        a2 = types.InlineKeyboardButton(text="2", callback_data="22")
        a3 = types.InlineKeyboardButton(text="3", callback_data="23")
        a4 = types.InlineKeyboardButton(text="4", callback_data="24")
        a5 = types.InlineKeyboardButton(text="5", callback_data="25")
        a6 = types.InlineKeyboardButton(text="6", callback_data="26")
        a7 = types.InlineKeyboardButton(text="7", callback_data="27")
        a8 = types.InlineKeyboardButton(text="8", callback_data="28")
        a9 = types.InlineKeyboardButton(text="9", callback_data="29")
        a10 = types.InlineKeyboardButton(text="10", callback_data="210")
        a11 = types.InlineKeyboardButton(text="11", callback_data="211")
        a12 = types.InlineKeyboardButton(text="12", callback_data="212")
        key.add(a1, a2, a3, a4, a5, a6)
        key.add(a7, a8, a9, a10, a11, a12)
        await message.answer("Семестр", reply_markup=key)
    elif message.text == buttons_ua_1[2] or message.text == buttons_ru_1[2]:
        key = types.InlineKeyboardMarkup()
        a1 = types.InlineKeyboardButton(text="1", callback_data="31")
        a2 = types.InlineKeyboardButton(text="2", callback_data="32")
        a3 = types.InlineKeyboardButton(text="3", callback_data="33")
        a4 = types.InlineKeyboardButton(text="4", callback_data="34")
        a5 = types.InlineKeyboardButton(text="5", callback_data="35")
        a6 = types.InlineKeyboardButton(text="6", callback_data="36")
        a7 = types.InlineKeyboardButton(text="7", callback_data="37")
        a8 = types.InlineKeyboardButton(text="8", callback_data="38")
        a9 = types.InlineKeyboardButton(text="9", callback_data="39")
        a10 = types.InlineKeyboardButton(text="10", callback_data="310")
        a11 = types.InlineKeyboardButton(text="11", callback_data="311")
        a12 = types.InlineKeyboardButton(text="12", callback_data="312")
        key.add(a1, a2, a3, a4, a5, a6)
        key.add(a7, a8, a9, a10, a11, a12)
        await message.answer("Семестр", reply_markup=key)
    elif message.text == buttons_ua_1[6] or message.text == buttons_ru_1[6]:
        key = types.InlineKeyboardMarkup()
        a1 = types.InlineKeyboardButton(text="1", callback_data="41")
        a2 = types.InlineKeyboardButton(text="2", callback_data="42")
        a3 = types.InlineKeyboardButton(text="3", callback_data="43")
        a4 = types.InlineKeyboardButton(text="4", callback_data="44")
        a5 = types.InlineKeyboardButton(text="5", callback_data="45")
        a6 = types.InlineKeyboardButton(text="6", callback_data="46")
        a7 = types.InlineKeyboardButton(text="7", callback_data="47")
        a8 = types.InlineKeyboardButton(text="8", callback_data="48")
        a9 = types.InlineKeyboardButton(text="9", callback_data="49")
        a10 = types.InlineKeyboardButton(text="10", callback_data="410")
        a11 = types.InlineKeyboardButton(text="11", callback_data="411")
        a12 = types.InlineKeyboardButton(text="12", callback_data="412")
        key.add(a1, a2, a3, a4, a5, a6)
        key.add(a7, a8, a9, a10, a11, a12)
        await message.answer("Семестр", reply_markup=key)
    elif message.text == buttons_ua_1[4]:
        key = types.InlineKeyboardMarkup()
        a1 = types.InlineKeyboardButton(text="1", callback_data="51")
        a2 = types.InlineKeyboardButton(text="2", callback_data="52")
        key.add(a1, a2)
        await message.answer("Тиждень", reply_markup=key)
    elif message.text == buttons_ru_1[4]:
        key = types.InlineKeyboardMarkup()
        a1 = types.InlineKeyboardButton(text="1", callback_data="51")
        a2 = types.InlineKeyboardButton(text="2", callback_data="52")
        key.add(a1, a2)
        await message.answer("Неделя", reply_markup=key)
    elif message.text == buttons_ua_1[3] or message.text == buttons_ru_1[3]:
        await page_3(message)
    elif message.text == buttons_ua_1[5] or message.text == buttons_ru_1[5]:
        await page_sport(message)
    elif message.text == buttons_ua_2[0] or message.text == buttons_ru_2[0]:
        await page_6(message)
    elif message.text == buttons_ua_2[1] or message.text == buttons_ru_2[1]:
        await send_pdf(message)
    elif message.text == buttons_ua_2[3]:
        await change_lang(message, 'ru')
    elif message.text == buttons_ru_2[3]:
        await change_lang(message, 'ua')
    elif message.text == buttons_ua_1[7]:
        await message.answer(buttons_ua_1[7], reply_markup=keyboard_ua_2())
    elif message.text == buttons_ru_1[7]:
        await message.answer(buttons_ru_1[7], reply_markup=keyboard_ru_2())
    elif message.text == buttons_ua_2[4]:
        await message.answer(buttons_ua_2[4], reply_markup=keyboard_ua_1())
    elif message.text == buttons_ru_2[4]:
        await message.answer(buttons_ru_2[4], reply_markup=keyboard_ru_1())


async def authentication(message, first=False, skip=False):
    findQuery = "SELECT mail, pass, stud_id, lang, group_id FROM users WHERE user_id=(%s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(findQuery, [message.chat.id])
        auth = cursor.fetchone()
    if skip:
        return auth
    if first:
        if auth:
            lang = auth[3]
            with open(c.strings_file, encoding='utf-8') as f:
                strings = json.load(f)
            keyboard = keyboard_ua_1()
            if lang == 'ru': keyboard = keyboard_ru_1()
            await message.answer(strings[lang]['auth_err_1'], reply_markup=keyboard)
    else:
        if not auth:
            await message.answer("Помилка аутентифікації, повторіть спробу входу")
            await reg_key(message)
    return auth


async def check_credentials(message, response):
    response_json = json.loads(response.text)
    if not response_json:
        await message.answer("*Введіть email і пароль від особистого кабінету*\n\nНаприклад:\ndemo@gmail.com d2v8F3", parse_mode="Markdown")
        await Form.authorization.set()
        return True


@dp.message_handler(content_types=['text'], state=Form.authorization)
async def registration(message: types.Message, state: FSMContext):
    s = message.text
    await state.finish()
    try:
        mail = s.split()[0]
        passwd = s.split()[1]
    except IndexError:
        await message.answer("Невірний формат")
        return
    page = "1"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)
    if not answer:
        await message.answer("Неправильний email або пароль")
        return
    student_id = answer[0]['st_cod']
    group_id = answer[0]['gid']
    selectQuery = "SELECT EXISTS (SELECT ID FROM users WHERE user_id=(%s))"
    inputQuery = "INSERT INTO users (user_id, stud_id, group_id, mail, pass) VALUES (%s, %s, %s, %s, %s)"
    updateQuery = "UPDATE users SET mail=(%s), pass=(%s) WHERE user_id=(%s)"
    selectUserQuery = "SELECT ID FROM users WHERE user_id=(%s)"
    existsRecBookQuery = "SELECT EXISTS (SELECT ID FROM record_book WHERE user_id=(%s) AND subj_id=(%s) AND semester=(%s))"
    insertRecBookQuery = "INSERT INTO record_book (user_id, subj_id, semester) VALUES (%s, %s, %s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(selectQuery, [message.chat.id])
        exists = cursor.fetchone()[0]
        if exists:
            cursor.executemany(updateQuery, [(mail, passwd, message.chat.id)])
        else:
            cursor.executemany(inputQuery, [(message.chat.id, student_id, group_id, mail, passwd)])
        conn.commit()
    await message.answer("Вхід успішно виконаний!", reply_markup=keyboard_ua_1())
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(selectUserQuery, [message.chat.id])
        user_id = cursor.fetchone()[0]
    for sem in range(1, 13):
        response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page=2&semestr={sem}')
        if not response:
            continue
        rec_book = json.loads(response.text)
        if not rec_book:
            break
        for a in rec_book:
            mark = a['oc_bol']
            if mark:
                continue
            subj_id = int(a['subj_id'])
            with DatabaseConnection() as db:
                conn, cursor = db
                cursor.executemany(existsRecBookQuery, [(user_id, subj_id, sem)])
                exists = cursor.fetchone()[0]
                if exists == 0:
                    cursor.executemany(insertRecBookQuery, [(user_id, subj_id, sem)])
                    conn.commit()


async def page_1(message):
    auth = await authentication(message)
    if not auth: return
    mail = auth[0]
    passwd = auth[1]
    lang = auth[3]
    page = "1"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    if not response:
        await message.answer(req_err_msg)
        return
    if await check_credentials(message, response): return
    answer = json.loads(response.text)[0]

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    main_page = strings[lang]['page_1'].format(**answer).replace("`", "'")
    await message.answer(main_page, parse_mode="Markdown")


async def page_2(message, sem):
    auth = await authentication(message)
    if not auth: return
    mail = auth[0]
    passwd = auth[1]
    lang = auth[3]
    page = "2"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return
    with_mark = len(answer)
    subjects = ""
    for a in answer:
        control = strings[lang]['page_2_exam']
        if a['control'] == "З": control = strings[lang]['page_2_zach']
        hvost = a['if_hvost']
        if not hvost: hvost = "—"
        ball = "{oc_short}{oc_ects} {oc_bol}".format(**a)
        if ball == " ":
            ball = "—"
            with_mark -= 1

        subjects = strings[lang]['page_2'].format(subjects, a['subject'], ball, control, a['credit'], hvost).replace("`", "'")

    key_histogram = None
    if with_mark > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(strings[lang]['histogram'], callback_data="histogram2" + sem))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


async def page_5(message, sem):
    auth = await authentication(message)
    if not auth: return
    mail = auth[0]
    passwd = auth[1]
    student_id = auth[2]
    lang = auth[3]
    page = "5"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return
    all_in_list = len(answer)
    for a in answer:
        if int(a['studid']) == student_id:
            rang1 = strings[lang]['page_5'].format(a['n'], all_in_list, a['sbal100'], a['sbal5'])
            num = int(a['n'])
            break
    else:
        await show_all_list(message, sem)
        return
    percent = float("%.2f" % (num * 100 / all_in_list))
    percent_str = strings[lang]['page_5_rate'].format(percent)
    stip = strings[lang]['page_5_stp']
    if percent < 50:
        if percent < 45:
            if percent < 40:
                stip += "100 %"
            else: stip += strings[lang]['page_5_probability']['high']
        else: stip += strings[lang]['page_5_probability']['low']
    else: stip += strings[lang]['page_5_probability']['zero']

    ps = strings[lang]['page_5_ps']
    key_extend = types.InlineKeyboardMarkup()
    key_extend.add(types.InlineKeyboardButton(strings[lang]['page_5_all_list'], callback_data="all_list" + sem))
    await message.answer(rang1 + percent_str + stip + ps, parse_mode="Markdown", reply_markup=key_extend)


async def page_4(message, sem):
    auth = await authentication(message)
    if not auth: return
    mail = auth[0]
    passwd = auth[1]
    lang = auth[3]
    page = "4"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return
    subjects = "*Курс {kurs}, семестр {semestr}:*\n\n".format(**answer[0])
    for i, a in enumerate(answer):
        control = strings[lang]['page_2_exam']
        if a['control'] == "З": control = strings[lang]['page_2_zach']
        subjects = strings[lang]['page_4'].format(subjects, i + 1, a['subject'], a['audit'], a['credit'], control).replace("`", "'")

    key_histogram = None
    if len(answer) > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(strings[lang]['histogram'], callback_data="histogram4" + sem))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


async def page_3(message):
    auth = await authentication(message)
    if not auth: return
    mail = auth[0]
    passwd = auth[1]
    lang = auth[3]
    page = "3"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return
    subjects = ""
    for a in answer:
        subjects = strings[lang]['page_3'].format(subjects, a['subject'], a['prepod'], a['data']).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


async def page_6(message):
    auth = await authentication(message)
    if not auth: return
    mail = auth[0]
    passwd = auth[1]
    lang = auth[3]
    page = "6"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return
    subjects = strings[lang]['page_6_header'].format(answer[0]['dog_name'], answer[0]['start_date'], answer[0]['dog_price'])
    for a in answer:
        subjects = strings[lang]['page_6'].format(subjects, a['term_start'], a['paid_date'], a['paid_value'], a['dp_id']).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


async def page_academic_schedule(message, week_num):
    auth = await authentication(message)
    if not auth: return
    lang = auth[3]
    gid = auth[4]

    week = '' if week_num == '1' else '2'
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/Schedule{week}/{gid}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return

    week_name = 'Тиждень' if lang == 'ua' else 'Неделя'
    subjects = f"📆 *{week_name} {week_num}*\n\n"
    days_sub = answer['Monday'], answer['Tuesday'], answer['Wednesday'], answer['Thursday'], answer['Friday']
    days_name_ua = ('Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця")
    days_name_ru = ('Понедельник', 'Вторник', 'Среда', 'Четверг', "Пятница")
    days_name = days_name_ua if lang == 'ua' else days_name_ru
    para_num = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣')
    para_name = ('Para1', 'Para2', 'Para3', 'Para4', 'Para5', 'Para6')
    for i, day in enumerate(days_sub):
        subjects = f"{subjects}*📌 {days_name[i]}*\n"
        for j, p_num in enumerate(para_num):
            para_json = day[para_name[j]]
            if para_json['Name']:
                name = para_json['Name'].replace('`', "'")
                prepod = para_json['Prepod'].replace('`', "'")
                para_data = f"*{name}* _{para_json['vid']}_\n➖ {para_json['Aud']} _({prepod})_"
                subjects = f"{subjects}{p_num} {para_data}\n"
        subjects = f"{subjects}➖➖➖➖➖➖➖➖➖➖➖➖\n"
    await message.answer(subjects, parse_mode='Markdown')


async def page_sport(message):
    auth = await authentication(message)
    if not auth: return
    lang = auth[3]
    response = mu.req_post('https://schedule.kpi.kharkov.ua/json/sport')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[lang]['not_found'])
        return
    key = types.InlineKeyboardMarkup()
    for a in answer:
        key.add(types.InlineKeyboardButton(a['sport'], callback_data="s{sportid}".format(**a)))
    await message.answer(strings[lang]['page_sport'], reply_markup=key)


def days(s_id):
    key = types.InlineKeyboardMarkup()
    but_1 = types.InlineKeyboardButton("Пн", callback_data=f"day1{s_id}")
    but_2 = types.InlineKeyboardButton("Вт", callback_data=f"day2{s_id}")
    but_3 = types.InlineKeyboardButton("Ср", callback_data=f"day3{s_id}")
    but_4 = types.InlineKeyboardButton("Чт", callback_data=f"day4{s_id}")
    but_5 = types.InlineKeyboardButton("Пт", callback_data=f"day5{s_id}")
    but_6 = types.InlineKeyboardButton("Сб", callback_data=f"day6{s_id}")
    but_7 = types.InlineKeyboardButton("Нд", callback_data=f"day7{s_id}")
    key.add(but_1, but_2, but_3)
    key.add(but_4, but_5)
    key.add(but_6, but_7)
    return key


def get_sport_schedule(s_id, day):
    day_names = ["", "Понеділок", "Вівторок", "Середа", "Четвер", "П`ятниця", "Субота", "Неділя"]
    day = day_names[day]
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/sport?sport_id={s_id}')
    if not response:
        return
    answer = json.loads(response.text)
    text = f"{day}:\n\n"
    for a in answer:
        if a['day'] == day:
            text += "{time} — {prepod}\n".format(**a)
    return text


async def send_pdf(message):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    url = f'http://schedule.kpi.kharkov.ua/json/getpdf?email={mail}&pass={passwd}'
    await bot.send_document(message.chat.id, url)


async def change_lang(message, lang):
    changeQuery = f"UPDATE users SET lang=(%s) WHERE user_id=(%s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.executemany(changeQuery, [(lang, message.chat.id)])
        conn.commit()
    if lang == 'ua':
        text = "Обрана українська мова"
        keyboard = keyboard_ua_2()
    else:
        text = "Выбран русский язык"
        keyboard = keyboard_ru_2()
    await message.answer(text, reply_markup=keyboard)


async def show_all_list(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    student_id = auth[2]
    lang = auth[3]
    page = "5"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)
    text = ""
    for a in answer:
        n = a['n']
        fio = a['fio']
        sbal100 = "%.1f" % float(a['sbal100'])
        if int(a['studid']) == student_id:
            text += f"⭐ *{fio} ➖ {sbal100}*\n"
        else:
            text += f"*{n}.* {fio} ➖ {sbal100}\n"
    text = text.replace('`', "'")
    if not text:
        with open(c.strings_file, encoding='utf-8') as f:
            strings = json.load(f)
        text = strings[lang]['not_found']
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")


async def send_histogram_of_page_2(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "2"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)
    subject = []
    score = []
    count = 0
    for n in answer:
        if not n['oc_bol'].isdigit():
            continue
        score.append(int(n['oc_bol']))
        subject.append(n['subject'])
        count += 1
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page=1')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)[0]
    histogram.histogram(count, score, subject, "{fam} {imya}\n{otch}".format(**answer))
    with open("media/img.png", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


async def send_histogram_of_page_4(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "4"
    response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    if not response:
        await message.answer(req_err_msg)
        return
    answer = json.loads(response.text)
    subject = []
    score = []
    count = 0
    for n in answer:
        score.append(int(float(n['credit']))) if n['credit'] else score.append(0)
        subject.append(n['subject'])
        count += 1
    histogram.histogram(count, score, subject, f"Семестр {sem}")
    with open("media/img.png", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


@dp.callback_query_handler(lambda callback_query: True)
async def callback_inline(callback_query: types.CallbackQuery):
    data = str(callback_query.data)
    if data[0] == "1":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_1(callback_query.message)
    elif data[0] == "2":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_2(callback_query.message, data[1:])
    elif data[0] == "3":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_5(callback_query.message, data[1:])
    elif data[0] == "4":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_4(callback_query.message, data[1:])
    elif data[0] == "5":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_academic_schedule(callback_query.message, data[1:])

    elif data[0] == "s":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        s_id = data[1:]
        response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/sport?sport_id={s_id}')
        if not response:
            try: await callback_query.answer(req_err_msg, show_alert=True)
            except utils.exceptions.InvalidQueryID: pass
            return
        answer = json.loads(response.text)
        if not answer:
            try: await callback_query.answer("Не найдено", show_alert=True)
            except utils.exceptions.InvalidQueryID: pass
            return
        schedule = get_sport_schedule(s_id, 1)
        if not schedule:
            try: await callback_query.answer(req_err_msg, show_alert=True)
            except utils.exceptions.InvalidQueryID: pass
            return
        await callback_query.message.answer(schedule, reply_markup=days(s_id))

    elif data[:3] == "day":
        day = int(data[3])
        s_id = data[4:]
        try:
            schedule = get_sport_schedule(s_id, day)
            if not schedule:
                try: await callback_query.answer(req_err_msg, show_alert=True)
                except utils.exceptions.InvalidQueryID: pass
                return
            await bot.edit_message_text(schedule, callback_query.from_user.id,
                                        callback_query.message.message_id, callback_query.from_user.id, reply_markup=days(s_id))
        except utils.exceptions.MessageNotModified: pass

    elif data[:8] == "all_list":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        sem = data[8:]
        await show_all_list(callback_query.message, sem)

    elif data[:10] == "histogram2":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        sem = data[10:]
        await send_histogram_of_page_2(callback_query.message, sem)

    elif data[:10] == "histogram4":
        await mu.delete_message(bot.delete_message, utils, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        sem = data[10:]
        await send_histogram_of_page_4(callback_query.message, sem)


if __name__ == '__main__':
    if not DEBUG:
        dp.loop.create_task(record_book.updater())
        dp.loop.create_task(record_book.update_users())
    executor.start_polling(dp, skip_updates=True)
