#!/usr/bin/env python
import json
from asyncio import sleep, get_event_loop
import constants as c
import my_utils as mu
import histogram
from database_connection import DatabaseConnection
import updaters
import news_parser

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import exceptions, callback_data


bot = Bot(c.token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup): authorization = State()
class Feedback(StatesGroup): text = State()
class SendMessageToUsers(StatesGroup): text = State()
class SearchStudent(StatesGroup): user = State()
class GetNews(StatesGroup): processing = State()


sign_in_butt = "👥 Увійти в кабінет"
buttons_ua_1 = ["ℹ Загальна інформація", "📕 Залікова книжка", "📊 Рейтинг", "⚠ Борги", "📆 Розклад занять", "📆 Розклад спорт. каф.", "🗓 Навчальний план", "➡ Далі"]
buttons_ru_1 = ["ℹ Общая информация", "📕 Зачётная книжка", "📊 Рейтинг", "⚠ Долги", "📆 Расписание занятий", "📆 Расписание спорт. каф.", "🗓 Учебный план", "➡ Дальше"]
buttons_ua_2 = ["💳 Оплати за навчання", "📄 Семестровий план", "🔍 Пошук студентів", "📨 Новини кафедри", "❓Підтримка", "🇺🇦 Мова", "⬅ Назад"]
buttons_ru_2 = ["💳 Оплаты за обучение", "📄 Семестровый план", "🔍 Поиск студентов", "📨 Новости кафедры", "❓Помощь", "🇷🇺 Язык", "⬅  Назад"]
req_err_msg = "😔 Не вдалося виконати запит, спробуйте пізніше"
auth_err_msg = "Помилка аутентифікації, повторіть спробу входу"
greetings_text = "*Введіть email і пароль від особистого кабінету*\n\nНаприклад:\ndemo@gmail.com d2v8F3"


def reply_keyboard(key_type: int):
    buttons = None
    if key_type == mu.Keyboards.UA_1:
        buttons = buttons_ua_1
    elif key_type == mu.Keyboards.UA_2:
        buttons = buttons_ua_2
    elif key_type == mu.Keyboards.RU_1:
        buttons = buttons_ru_1
    elif key_type == mu.Keyboards.RU_2:
        buttons = buttons_ru_2
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
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


@dp.message_handler(commands=['start'])
async def handle_text(message: types.Message):
    await reg_key(message)


async def reg_key(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
    key.add(sign_in_butt, buttons_ua_2[4])
    await message.answer("Щоб продовжити натисніть на одну з кнопок", reply_markup=key)


@dp.message_handler(commands=['feedback'])
async def handle_text(message: types.Message):
    auth = await authentication(message, skip=True)
    lang = auth[mu.ResTypes.LANG] if auth else 'ua'
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    await message.reply(strings[lang]['feedback_start'])
    await Feedback.text.set()


@dp.message_handler(content_types=[types.ContentType.ANY], state=Feedback.text)
async def feedback(message: types.Message, state: FSMContext):
    await state.finish()
    auth = await authentication(message, skip=True)
    lang = auth[mu.ResTypes.LANG] if auth else 'ua'
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if message.text:
        for exception in ['/exit', sign_in_butt], buttons_ua_1, buttons_ru_1:
            if message.text in exception:
                await message.reply(strings[lang]['cancel'])
                return
    name = mu.esc_markdown(message.from_user.full_name)
    username = mu.esc_markdown(message.from_user.username)
    text = f"*Feedback!\n\nUser:* [{name}](tg://user?id={message.from_user.id})\n" \
           f"*UserName:* @{username}\n*ID:* {message.from_user.id}"
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
    except exceptions.CantParseEntities:
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
    len_users = len(users)
    progress_message = (await message.answer(f'0/{len_users}')).message_id
    for n, user in enumerate(users, 1):
        if await mu.send_message(bot.send_message, exceptions, chat_id=user[0], text=message.text, parse_mode='Markdown'):
            i += 1
        else:
            j += 1
        await bot.edit_message_text(f'{n}/{len_users}', message.chat.id, progress_message)
        await sleep(.1)
    await message.answer(f"Отправлено: {i}\nНе отправлено: {j}")


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message, state: FSMContext):
    if message.text == sign_in_butt:
        auth = await authentication(message, first=True)
        if auth:
            return
        await message.answer(greetings_text, parse_mode="Markdown")
        await Form.authorization.set()
    elif message.text == buttons_ua_2[4]:
        await message.answer(c.helper_ua, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == buttons_ru_2[4]:
        await message.answer(c.helper_ru, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == buttons_ua_1[0] or message.text == buttons_ru_1[0]:
        await page_1(message)
    elif message.text == buttons_ua_1[1] or message.text == buttons_ru_1[1]:
        await message.answer("Семестр", reply_markup=generate_inline_keyboard(mu.CallbackFuncs.PAGE_2, 12))
    elif message.text == buttons_ua_1[2] or message.text == buttons_ru_1[2]:
        await message.answer("Семестр", reply_markup=generate_inline_keyboard(mu.CallbackFuncs.PAGE_5, 12))
    elif message.text == buttons_ua_1[6] or message.text == buttons_ru_1[6]:
        await message.answer("Семестр", reply_markup=generate_inline_keyboard(mu.CallbackFuncs.PAGE_4, 12))
    elif message.text == buttons_ua_1[4]:
        await message.answer("Тиждень", reply_markup=generate_inline_keyboard(mu.CallbackFuncs.SCHEDULE, 2))
    elif message.text == buttons_ru_1[4]:
        await message.answer("Неделя", reply_markup=generate_inline_keyboard(mu.CallbackFuncs.SCHEDULE, 2))
    elif message.text == buttons_ua_1[3] or message.text == buttons_ru_1[3]:
        await page_3(message)
    elif message.text == buttons_ua_1[5] or message.text == buttons_ru_1[5]:
        await page_sport(message)
    elif message.text == buttons_ua_2[0] or message.text == buttons_ru_2[0]:
        await page_6(message)
    elif message.text == buttons_ua_2[1] or message.text == buttons_ru_2[1]:
        await send_pdf(message)
    elif message.text == buttons_ua_2[5]:
        await change_lang(message, 'ru')
    elif message.text == buttons_ru_2[5]:
        await change_lang(message, 'ua')
    elif message.text == buttons_ua_1[7]:
        await message.answer(buttons_ua_1[7], reply_markup=reply_keyboard(mu.Keyboards.UA_2))
    elif message.text == buttons_ru_1[7]:
        await message.answer(buttons_ru_1[7], reply_markup=reply_keyboard(mu.Keyboards.RU_2))
    elif message.text == buttons_ua_2[6]:
        await message.answer(buttons_ua_2[6], reply_markup=reply_keyboard(mu.Keyboards.UA_1))
    elif message.text == buttons_ru_2[6]:
        await message.answer(buttons_ru_2[6], reply_markup=reply_keyboard(mu.Keyboards.RU_1))
    elif message.text == buttons_ua_2[2] or message.text == buttons_ru_2[2]:
        await search_students(message)
    elif message.text == buttons_ua_2[3] or message.text == buttons_ru_2[3]:
        await GetNews.processing.set()
        try: await get_news(message)
        finally: await state.finish()


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
            with open(c.strings_file, encoding='utf-8') as f:
                strings = json.load(f)
            key_type = mu.Keyboards.UA_1
            if auth[mu.ResTypes.LANG] == 'ru':
                key_type = mu.Keyboards.RU_1
            await message.answer(strings[auth[mu.ResTypes.LANG]]['auth_err_1'], reply_markup=reply_keyboard(key_type))
    else:
        if not auth:
            await message.answer(auth_err_msg)
            await reg_key(message)
    return auth


async def api_request(message=None, path=c.api_cab, **kwargs):
    args = ''
    for arg in kwargs:
        args += f'&{arg.replace("passwd", "pass", 1)}={kwargs[arg]}'
    args = '?' + args[1:]
    response = mu.req_post(c.api_url + path + args)
    if not response:
        if message:
            await message.answer(req_err_msg)
        return
    return json.loads(response.text)


@dp.message_handler(content_types=['text'], state=Form.authorization)
async def registration(message: types.Message, state: FSMContext):
    await state.finish()
    s = message.text.split()
    if len(s) != 2:
        await message.answer("Невірний формат")
        return
    mail, passwd = s
    answer = await api_request(message, email=mail, passwd=passwd, page=1)
    if answer is None: return
    if not answer:
        await message.answer("Неправильний email або пароль")
        return
    student_id = answer[0]['st_cod']
    group_id = answer[0]['gid']
    f_name = answer[0]['imya']
    l_name = answer[0]['fam']
    faculty = answer[0]['grupa'].split('-')[0]
    selectQuery = "SELECT EXISTS (SELECT ID FROM users WHERE user_id=(%s))"
    insertQuery = "INSERT INTO users (user_id, stud_id, group_id, mail, pass, f_name, l_name, faculty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
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
            cursor.executemany(insertQuery, [(message.chat.id, student_id, group_id, mail, passwd, f_name, l_name, faculty)])
        conn.commit()
    await message.answer("Вхід успішно виконаний!", reply_markup=reply_keyboard(mu.Keyboards.UA_1))
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.execute(selectUserQuery, [message.chat.id])
        user_id = cursor.fetchone()[0]
    for sem in range(1, 13):
        rec_book = await api_request(message, email=mail, passwd=passwd, page=2, semestr=sem)
        if rec_book is None:
            continue
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
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=1)
    if answer is None: return
    if not answer:
        await message.answer(auth_err_msg)
        await message.answer(greetings_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
        await Form.authorization.set()
        return
    answer = answer[0]

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    main_page = strings[auth[mu.ResTypes.LANG]]['page_1'].format(**answer).replace("`", "'")
    await message.answer(main_page, parse_mode="Markdown")


async def page_2(message, sem):
    auth = await authentication(message)
    if not auth: return
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=2, semestr=sem)
    if answer is None: return

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    with_mark = len(answer)
    subjects = ''
    for a in answer:
        control = strings[auth[mu.ResTypes.LANG]]['page_2_exam']
        if a['control'] == "З": control = strings[auth[mu.ResTypes.LANG]]['page_2_zach']
        hvost = a['if_hvost']
        if not hvost: hvost = "—"
        ball = "{oc_short}{oc_ects} {oc_bol}".format(**a)
        if ball == " ":
            ball = "—"
            with_mark -= 1
        subjects = strings[auth[mu.ResTypes.LANG]]['page_2'] \
            .format(subjects, a['subject'], ball, control, a['credit'], hvost).replace("`", "'")

    key_histogram = None
    if with_mark > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(strings[auth[mu.ResTypes.LANG]]['histogram'],
                                                     callback_data=set_callback(mu.CallbackFuncs.HISTOGRAM_2, sem)))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


async def page_5(message, sem):
    auth = await authentication(message)
    if not auth: return
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=5, semestr=sem)
    if answer is None: return

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    all_in_list = len(answer)
    for a in answer:
        if int(a['studid']) == auth[mu.ResTypes.STUD_ID]:
            rang1 = strings[auth[mu.ResTypes.LANG]]['page_5'].format(a['n'], all_in_list, a['sbal100'], a['sbal5'])
            num = int(a['n'])
            break
    else:
        await show_all_list(message, sem, contract=True)
        return
    percent = float("%.2f" % (num * 100 / all_in_list))
    percent_str = strings[auth[mu.ResTypes.LANG]]['page_5_rate'].format(percent)
    stip = strings[auth[mu.ResTypes.LANG]]['page_5_stp']
    if percent < 50:
        if percent < 45:
            if percent < 40:
                stip += "100 %"
            else: stip += strings[auth[mu.ResTypes.LANG]]['page_5_probability']['high']
        else: stip += strings[auth[mu.ResTypes.LANG]]['page_5_probability']['low']
    else: stip += strings[auth[mu.ResTypes.LANG]]['page_5_probability']['zero']

    ps = strings[auth[mu.ResTypes.LANG]]['page_5_ps']
    key_extend = types.InlineKeyboardMarkup()
    key_extend.add(types.InlineKeyboardButton(strings[auth[mu.ResTypes.LANG]]['page_5_all_list'],
                                              callback_data=set_callback(mu.CallbackFuncs.RATING_SHOW_ALL, sem)))
    await message.answer(rang1 + percent_str + stip + ps, parse_mode="Markdown", reply_markup=key_extend)


async def page_4(message, sem):
    auth = await authentication(message)
    if not auth: return
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=4, semestr=sem)
    if answer is None: return

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    subjects = "*Курс {kurs}, семестр {semestr}:*\n\n".format(**answer[0])
    for i, a in enumerate(answer):
        control = strings[auth[mu.ResTypes.LANG]]['page_2_exam']
        if a['control'] == "З": control = strings[auth[mu.ResTypes.LANG]]['page_2_zach']
        subjects = strings[auth[mu.ResTypes.LANG]]['page_4'] \
            .format(subjects, i + 1, a['subject'], a['audit'], a['credit'], control).replace("`", "'")

    key_histogram = None
    if len(answer) > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(strings[auth[mu.ResTypes.LANG]]['histogram'],
                                                     callback_data=set_callback(mu.CallbackFuncs.HISTOGRAM_4, sem)))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


async def page_3(message):
    auth = await authentication(message)
    if not auth: return
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=3)
    if answer is None: return

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    subjects = ''
    for a in answer:
        subjects = strings[auth[mu.ResTypes.LANG]]['page_3'] \
            .format(subjects, a['subject'], a['prepod'], a['data']).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


async def page_6(message):
    auth = await authentication(message)
    if not auth: return
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=6)
    if answer is None: return

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    subjects = strings[auth[mu.ResTypes.LANG]]['page_6_header'] \
        .format(answer[0]['dog_name'], answer[0]['start_date'], answer[0]['dog_price'])
    for a in answer:
        subjects = strings[auth[mu.ResTypes.LANG]]['page_6'] \
            .format(subjects, a['term_start'], a['paid_date'], a['paid_value'], a['dp_id']).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


async def page_academic_schedule(message, week_num):
    auth = await authentication(message)
    if not auth: return
    week = '' if week_num == 1 else '2'
    answer = await api_request(message, path=f'{c.api_sched}{week}/{auth[mu.ResTypes.GROUP_ID]}')
    if answer is None: return
    with open(c.strings_file, encoding='utf-8') as f:

        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return

    week_name = 'Тиждень' if auth[mu.ResTypes.LANG] == 'ua' else 'Неделя'
    subjects = f"📆 *{week_name} {week_num}*\n\n"
    days_sub = answer['Monday'], answer['Tuesday'], answer['Wednesday'], answer['Thursday'], answer['Friday']
    days_name_ua = ('Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця")
    days_name_ru = ('Понедельник', 'Вторник', 'Среда', 'Четверг', "Пятница")
    days_name = days_name_ua if auth[mu.ResTypes.LANG] == 'ua' else days_name_ru
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
    answer = await api_request(message, path=c.api_sport)
    if answer is None: return

    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not answer:
        await message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    key = types.InlineKeyboardMarkup()
    for a in answer:
        key.add(types.InlineKeyboardButton(a['sport'], callback_data=set_callback(mu.CallbackFuncs.SPORT_TYPE, a['sportid'])))
    await message.answer(strings[auth[mu.ResTypes.LANG]]['page_sport'], reply_markup=key)


def get_days_keyboard(s_id):
    days = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд')
    buttons = []
    key = types.InlineKeyboardMarkup()
    for day in range(len(days)):
        buttons.append(types.InlineKeyboardButton(days[day],
                       callback_data=set_callback(mu.CallbackFuncs.SPORT_DAY, {'day': day, 'id': s_id})))
    key.add(*buttons[0:3])
    key.add(*buttons[3:5])
    key.add(*buttons[5:])
    return key


async def get_sport_schedule(s_id, day=0):
    day_names = ("Понеділок", "Вівторок", "Середа", "Четвер", "П`ятниця", "Субота", "Неділя")
    day = day_names[day]
    answer = await api_request(path=c.api_sport, sport_id=s_id)
    if answer is None: return
    text = f"{day}:\n\n"
    for a in answer:
        if a['day'] == day:
            text += "{time} — {prepod}\n".format(**a)
    return text


async def send_pdf(message):
    auth = await authentication(message)
    if not auth: return
    url = f'{c.api_url}{c.api_doc}?email={auth[mu.ResTypes.MAIL]}&pass={auth[mu.ResTypes.PASS]}'
    await bot.send_document(message.chat.id, url)


async def change_lang(message, lang):
    changeQuery = f"UPDATE users SET lang=(%s) WHERE user_id=(%s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.executemany(changeQuery, [(lang, message.chat.id)])
        conn.commit()
    if lang == 'ua':
        text = "Обрана українська мова"
        key_type = mu.Keyboards.UA_2
    else:
        text = "Выбран русский язык"
        key_type = mu.Keyboards.RU_2
    await message.answer(text, reply_markup=reply_keyboard(key_type))


async def calculate_mark(auth, sem):
    subjects = await api_request(email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=2, semestr=sem)
    if subjects is None: return
    mark100 = mark5 = credits_ = 0
    for subj in subjects:
        if not subj['oc_bol'] or not subj['credit']:
            continue
        mark100 += (int(subj['oc_bol']) * float(subj['credit']))
        credits_ += float(subj['credit'])
    mark100 = mark100 * 0.9 / credits_
    if mark100 >= 90:
        mark5 = 5
    elif mark100 >= 75:
        mark5 = 4
    elif mark5 >= 60:
        mark5 = 3
    return mark100, mark5


async def show_all_list(message, sem, sort=False, contract=False):
    auth = await authentication(message)
    if not auth: return False
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=5, semestr=sem)
    if answer is None: return
    text = ''
    if contract:
        sort = True
        mark = await calculate_mark(auth, sem)
        if not mark:
            await message.answer(req_err_msg)
            return
        main_info = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=1)
        if not main_info: return
        main_info = main_info[0]
        answer.append({'fio': f"{main_info['fam']} {main_info['imya'][0]}. {main_info['otch'][0]}.",
                       'group': main_info['grupa'], 'sbal5': mark[1], 'sbal100': mark[0], 'studid': main_info['st_cod']})
    if sort:
        answer = sorted(answer, key=lambda student: float(student['sbal100']), reverse=True)
    for n, a in enumerate(answer, 1):
        fio = a['fio']
        sbal100 = "%.1f" % float(a['sbal100'])
        if int(a['studid']) == auth[mu.ResTypes.STUD_ID]:
            text += f"⭐ *{fio.lstrip()} ➖ {sbal100}*\n"
        else:
            text += f"*{n}.* {fio.lstrip()} ➖ {sbal100}\n"
    text = text.replace('`', "'")
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not text:
        text = strings[auth[mu.ResTypes.LANG]]['not_found']
    key = types.InlineKeyboardMarkup()
    if not sort:
        key.add(types.InlineKeyboardButton(strings[auth[mu.ResTypes.LANG]]['rating_sort'],
                                           callback_data=set_callback(mu.CallbackFuncs.RATING_SHOW_ALL_SORT, sem)))
    await bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=key)


async def send_histogram_of_page_2(message, sem):
    auth = await authentication(message)
    if not auth: return False
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=2, semestr=sem)
    if answer is None: return
    subject = []
    score = []
    count = 0
    for n in answer:
        if not n['oc_bol'].isdigit():
            continue
        score.append(int(n['oc_bol']))
        subject.append(n['subject'])
        count += 1
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=1)
    if answer is None: return
    answer = answer[0]
    histogram.histogram(count, score, subject, "{fam} {imya}\n{otch}".format(**answer))
    with open("media/img.png", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


async def send_histogram_of_page_4(message, sem):
    auth = await authentication(message)
    if not auth: return False
    answer = await api_request(message, email=auth[mu.ResTypes.MAIL], passwd=auth[mu.ResTypes.PASS], page=4, semestr=sem)
    if answer is None: return
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


async def sport_select(callback_query, s_id):
    answer = await api_request(callback_query.message, path=c.api_sport, sport_id=s_id)
    if answer is None: return
    if not answer:
        auth = await authentication(callback_query.message)
        if not auth: return
        with open(c.strings_file, encoding='utf-8') as f:
            strings = json.load(f)
        await callback_query.message.answer(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    schedule = await get_sport_schedule(s_id)
    if not schedule:
        try: await callback_query.answer(req_err_msg, show_alert=True)
        except exceptions.InvalidQueryID: pass
        return
    await callback_query.message.answer(schedule, reply_markup=get_days_keyboard(s_id))


async def sport_day(callback_query, data):
    day = data.get('day')
    s_id = data.get('id')
    try:
        schedule = await get_sport_schedule(s_id, day)
        if not schedule:
            try: await callback_query.answer(req_err_msg, show_alert=True)
            except exceptions.InvalidQueryID: pass
            return
        await bot.edit_message_text(schedule, callback_query.from_user.id, callback_query.message.message_id,
                                    callback_query.from_user.id, reply_markup=get_days_keyboard(s_id))
    except exceptions.MessageNotModified: pass


async def search_students(message):
    auth = await authentication(message)
    if not auth: return False
    await SearchStudent.user.set()
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    await message.answer(strings[auth[mu.ResTypes.LANG]]['search_student'])


@dp.message_handler(content_types=types.ContentTypes.ANY, state=SearchStudent)
async def handle_text(message: types.Message, state: FSMContext):
    await state.finish()
    auth = await authentication(message)
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    if not auth: return False
    selectByIdQuery = "SELECT mail, pass FROM users WHERE user_id=(%s)"
    selectByFNQuery = "SELECT mail, pass FROM users WHERE f_name=(%s) AND l_name=(%s) GROUP BY stud_id"
    if message.forward_date:
        if not message.forward_from:
            await message.reply(strings[auth[mu.ResTypes.LANG]]['user_hidden'])
            return
        user_id = message.forward_from.id
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectByIdQuery, [user_id])
            result = cursor.fetchall()
    else:
        if not message.text:
            await message.reply(strings[auth[mu.ResTypes.LANG]]['wrong_format'])
            return
        if message.text in buttons_ua_1 + buttons_ua_2 + buttons_ru_1 + buttons_ru_2:
            await message.reply(strings[auth[mu.ResTypes.LANG]]['wrong_format'])
            return
        try:
            message.text.encode('utf-8')
        except UnicodeError:
            await message.reply(strings[auth[mu.ResTypes.LANG]]['wrong_format'])
            return
        s = message.text.replace('`', "'").split()
        if len(s) != 2:
            await message.reply(strings[auth[mu.ResTypes.LANG]]['wrong_format'])
            return
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.executemany(selectByFNQuery, [(s[0].capitalize(), s[1].capitalize())])
            result = cursor.fetchall()
    if not result:
        await message.reply(strings[auth[mu.ResTypes.LANG]]['not_found'])
        return
    for res in result:
        answer = await api_request(message, email=res[0], passwd=res[1], page=1)
        if answer is None: continue
        if not answer:
            await message.reply(strings[auth[mu.ResTypes.LANG]]['not_found'])
            continue
        main_page = strings[auth[mu.ResTypes.LANG]]['page_1'].format(**answer[0]).replace("`", "'")
        await message.reply(main_page, parse_mode='Markdown')
        await sleep(.05)


async def get_news(message):
    auth = await authentication(message)
    if not auth: return False
    with open(c.strings_file, encoding='utf-8') as f:
        strings = json.load(f)
    message_id = (await message.answer(strings[auth[mu.ResTypes.LANG]]['loading'])).message_id
    news = news_parser.parse_news(auth[mu.ResTypes.FACULTY], update_last=False)
    if not news:
        await bot.edit_message_text(strings[auth[mu.ResTypes.LANG]]['faculty_unsupported'], message.chat.id, message_id)
        return
    news_str = ''
    for i, post in enumerate(news.posts, 1):
        news_str += f'*{i}.* [{mu.esc_markdown(post.title)}]({mu.esc_markdown(post.link)})\n'
        if i == 10: break
    await bot.edit_message_text(news_str, message.chat.id, message_id, parse_mode='Markdown')


@dp.callback_query_handler(lambda callback_query: True)
async def callback_inline(callback_query: types.CallbackQuery):
    data = get_callback(callback_query.data)
    if data is None:
        return
    func, data = data
    if func == mu.CallbackFuncs.PAGE_1:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_1(callback_query.message)
    elif func == mu.CallbackFuncs.PAGE_2:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_2(callback_query.message, data)
    elif func == mu.CallbackFuncs.PAGE_5:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_5(callback_query.message, data)
    elif func == mu.CallbackFuncs.PAGE_4:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_4(callback_query.message, data)
    elif func == mu.CallbackFuncs.SCHEDULE:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_academic_schedule(callback_query.message, data)
    elif func == mu.CallbackFuncs.SPORT_TYPE:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await sport_select(callback_query, data)
    elif func == mu.CallbackFuncs.SPORT_DAY:
        await sport_day(callback_query, data)
    elif func == mu.CallbackFuncs.RATING_SHOW_ALL:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await show_all_list(callback_query.message, data)
    elif func == mu.CallbackFuncs.RATING_SHOW_ALL_SORT:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await show_all_list(callback_query.message, data, sort=True)
    elif func == mu.CallbackFuncs.HISTOGRAM_2:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await send_histogram_of_page_2(callback_query.message, data)
    elif func == mu.CallbackFuncs.HISTOGRAM_4:
        await mu.delete_message(bot.delete_message, exceptions, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await send_histogram_of_page_4(callback_query.message, data)


if __name__ == '__main__':
    if __debug__ is False:  # if -O flag is set
        loop = get_event_loop()
        loop.create_task(updaters.updater_record_book())
        loop.create_task(updaters.update_users_record_book())
        loop.create_task(updaters.updater_news())
    executor.start_polling(dp, skip_updates=True)
