#!/usr/bin/env python
from asyncio import sleep
from contextlib import suppress
from app import config, misc
from app.utils.my_utils import *
from app.utils import histogram, news_parser
from app.utils.database_connection import DatabaseConnection

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import exceptions
from aiogram.contrib.middlewares.i18n import I18nMiddleware


bot = Bot(config.TG_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

i18n = I18nMiddleware('bot', misc.locales_dir, default='ua')
dp.middleware.setup(i18n)
__ = i18n.gettext


class Form(StatesGroup): authorization = State()
class Feedback(StatesGroup): text = State()
class SendMessageToUsers(StatesGroup): text = State()
class SearchStudent(StatesGroup): user = State()
class GetNews(StatesGroup): processing = State()


@dp.message_handler(commands=['start'])
async def handle_text(message: types.Message):
    await reg_key(message)


@dp.message_handler(commands=['feedback'])
async def handle_text(message: types.Message):
    student = await authentication(message, skip=True)
    await message.reply(__('feedback_start', locale=student.lang))
    await Feedback.text.set()


@dp.message_handler(content_types=[types.ContentType.ANY], state=Feedback.text)
async def feedback(message: types.Message, state: FSMContext):
    await state.finish()
    student = await authentication(message, skip=True)
    if message.text:
        for exception in ['/exit', misc.sign_in_butt], misc.buttons_ua_1, misc.buttons_ru_1:
            if message.text in exception:
                await message.reply(__('cancel', locale=student.lang))
                return
    name = esc_markdown(message.from_user.full_name)
    username = esc_markdown(message.from_user.username)
    text = f"*Feedback!\n\nUser:* [{name}](tg://user?id={message.from_user.id})\n" \
           f"*UserName:* @{username}\n*ID:* {message.from_user.id}"
    await bot.send_message(config.BOT_ADMIN, text, parse_mode="Markdown")
    await bot.forward_message(config.BOT_ADMIN, message.chat.id, message.message_id)
    await message.answer(__('feedback_finish', locale=student.lang))


@dp.message_handler(commands=['send'])
async def handle_text(message: types.Message):
    if message.chat.id == config.BOT_ADMIN:
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
        if await send_message(bot.send_message, chat_id=user[0], text=message.text, parse_mode='Markdown'):
            i += 1
        else:
            j += 1
        await bot.edit_message_text(f'{n}/{len_users}', message.chat.id, progress_message)
        await sleep(.1)
    await message.answer(f"Отправлено: {i}\nНе отправлено: {j}")


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message, state: FSMContext):
    if message.text == misc.sign_in_butt:
        student = await authentication(message, first=True)
        if student:
            return
        await message.answer(misc.greetings_text, parse_mode="Markdown")
        await Form.authorization.set()
    elif message.text == misc.buttons_ua_2[4]:
        await message.answer(misc.helper_ua, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == misc.buttons_ru_2[4]:
        await message.answer(misc.helper_ru, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text == misc.buttons_ua_1[0] or message.text == misc.buttons_ru_1[0]:
        await page_1(message)
    elif message.text == misc.buttons_ua_1[1] or message.text == misc.buttons_ru_1[1]:
        await message.answer("Семестр", reply_markup=generate_inline_keyboard(CallbackFuncs.PAGE_2, 12))
    elif message.text == misc.buttons_ua_1[2] or message.text == misc.buttons_ru_1[2]:
        await message.answer("Семестр", reply_markup=generate_inline_keyboard(CallbackFuncs.PAGE_5, 12))
    elif message.text == misc.buttons_ua_1[6] or message.text == misc.buttons_ru_1[6]:
        await message.answer("Семестр", reply_markup=generate_inline_keyboard(CallbackFuncs.PAGE_4, 12))
    elif message.text == misc.buttons_ua_1[4]:
        await message.answer("Тиждень", reply_markup=generate_inline_keyboard(CallbackFuncs.SCHEDULE, 2))
    elif message.text == misc.buttons_ru_1[4]:
        await message.answer("Неделя", reply_markup=generate_inline_keyboard(CallbackFuncs.SCHEDULE, 2))
    elif message.text == misc.buttons_ua_1[3] or message.text == misc.buttons_ru_1[3]:
        await page_3(message)
    elif message.text == misc.buttons_ua_1[5] or message.text == misc.buttons_ru_1[5]:
        await page_sport(message)
    elif message.text == misc.buttons_ua_2[0] or message.text == misc.buttons_ru_2[0]:
        await page_6(message)
    elif message.text == misc.buttons_ua_2[1] or message.text == misc.buttons_ru_2[1]:
        await send_pdf(message)
    elif message.text == misc.buttons_ua_2[5]:
        await change_lang(message, 'ru')
    elif message.text == misc.buttons_ru_2[5]:
        await change_lang(message, 'ua')
    elif message.text == misc.buttons_ua_1[7]:
        await message.answer(misc.buttons_ua_1[7], reply_markup=reply_keyboard(Keyboards.UA_2))
    elif message.text == misc.buttons_ru_1[7]:
        await message.answer(misc.buttons_ru_1[7], reply_markup=reply_keyboard(Keyboards.RU_2))
    elif message.text == misc.buttons_ua_2[6]:
        await message.answer(misc.buttons_ua_2[6], reply_markup=reply_keyboard(Keyboards.UA_1))
    elif message.text == misc.buttons_ru_2[6]:
        await message.answer(misc.buttons_ru_2[6], reply_markup=reply_keyboard(Keyboards.RU_1))
    elif message.text == misc.buttons_ua_2[2] or message.text == misc.buttons_ru_2[2]:
        await search_students(message)
    elif message.text == misc.buttons_ua_2[3] or message.text == misc.buttons_ru_2[3]:
        await GetNews.processing.set()
        try: await get_news(message)
        finally: await state.finish()


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
    await message.answer("Вхід успішно виконаний!", reply_markup=reply_keyboard(Keyboards.UA_1))
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


@auth_student
@load_page(allow_invalid=True, page=1)
async def page_1(message, student: Student, api_data):
    if not api_data:
        await message.answer(misc.auth_err_msg)
        await message.answer(misc.greetings_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
        await Form.authorization.set()
        return
    main_page = __('page_1', locale=student.lang).format(**api_data[0]).replace("`", "'")
    await message.answer(main_page, parse_mode="Markdown")


@auth_student
@load_page(page=2)
async def page_2(message, sem, student: Student, api_data: list):
    with_mark = len(api_data)
    subjects = ''
    for a in api_data:
        control = __('page_2_exam', locale=student.lang)
        if a['control'] == "З": control = __('page_2_zach', locale=student.lang)
        hvost = a['if_hvost']
        if not hvost: hvost = "—"
        ball = "{oc_short}{oc_ects} {oc_bol}".format(**a)
        if ball == " ":
            ball = "—"
            with_mark -= 1
        subjects = __('page_2', locale=student.lang) \
            .format(subjects, a['subject'], ball, control, a['credit'], hvost).replace("`", "'")

    key_histogram = None
    if with_mark > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(__('histogram', locale=student.lang),
                                                     callback_data=set_callback(CallbackFuncs.HISTOGRAM_2, sem)))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


@auth_student
@load_page(page=5)
async def page_5(message, sem, student: Student, api_data: list):
    all_in_list = len(api_data)
    for a in api_data:
        if int(a['studid']) == student.id:
            rang1 = __('page_5', locale=student.lang).format(a['n'], all_in_list, a['sbal100'], a['sbal5'])
            num = int(a['n'])
            break
    else:
        await show_all_list(message, sem=sem, contract=True)
        return
    percent = float(num * 100 / all_in_list).__round__(2)
    percent_str = __('page_5_rate', locale=student.lang).format(percent)
    stip = __('page_5_stp', locale=student.lang)
    if percent < 50:
        if percent < 45:
            if percent < 40:
                stip += "100 %"
            else: stip += __('page_5_probability_high', locale=student.lang)
        else: stip += __('page_5_probability_low', locale=student.lang)
    else: stip += __('page_5_probability_zero', locale=student.lang)

    ps = __('page_5_ps', locale=student.lang)
    key_extend = types.InlineKeyboardMarkup()
    key_extend.add(types.InlineKeyboardButton(__('page_5_all_list', locale=student.lang),
                                              callback_data=set_callback(CallbackFuncs.RATING_SHOW_ALL, sem)))
    await message.answer(rang1 + percent_str + stip + ps, parse_mode="Markdown", reply_markup=key_extend)


@auth_student
@load_page(page=4)
async def page_4(message, sem, student: Student, api_data: list):
    subjects = "*Курс {kurs}, семестр {semestr}:*\n\n".format(**api_data[0])
    for i, a in enumerate(api_data):
        control = __('page_2_exam', locale=student.lang)
        if a['control'] == "З": control = __('page_2_zach', locale=student.lang)
        subjects = __('page_4', locale=student.lang) \
            .format(subjects, i + 1, esc_markdown(a['subject']), esc_markdown(a['audit']), esc_markdown(a['credit']), control)

    key_histogram = None
    if len(api_data) > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(__('histogram', locale=student.lang),
                                                     callback_data=set_callback(CallbackFuncs.HISTOGRAM_4, sem)))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


@auth_student
@load_page(page=3)
async def page_3(message, student: Student, api_data: list):
    subjects = ''
    for a in api_data:
        subjects = __('page_3', locale=student.lang) \
            .format(subjects, a['subject'], a['prepod'], a['data']).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


@auth_student
@load_page(page=6)
async def page_6(message, student: Student, api_data: list):
    subjects = __('page_6_header', locale=student.lang) \
        .format(api_data[0]['dog_name'], api_data[0]['start_date'], api_data[0]['dog_price'])
    for a in api_data:
        subjects = __('page_6', locale=student.lang) \
            .format(subjects, a['term_start'], a['paid_date'], a['paid_value'], a['dp_id']).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


@auth_student
async def page_academic_schedule(message, week_num, student: Student):
    week = '' if week_num == 1 else '2'
    api_data = await api_request(message, path=f'{misc.api_sched}{week}/{student.group_id}')
    if api_data is None: return
    if not api_data:
        await message.answer(__('not_found', locale=student.lang))
        return
    # TODO move to utils
    days_name_ua = ('Понеділок', 'Вівторок', 'Середа', 'Четвер', "П'ятниця")
    days_name_ru = ('Понедельник', 'Вторник', 'Среда', 'Четверг', "Пятница")
    para_num = ('1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣')
    para_name = ('Para1', 'Para2', 'Para3', 'Para4', 'Para5', 'Para6')
    week_name = days_name = None
    if student.lang == 'ua':
        week_name = 'Тиждень'
        days_name = days_name_ua
    elif student.lang == 'ru':
        week_name = 'Неделя'
        days_name = days_name_ru
    subjects = f"📆 *{week_name} {week_num}*\n\n"
    days_sub = api_data['Monday'], api_data['Tuesday'], api_data['Wednesday'], api_data['Thursday'], api_data['Friday']
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


@auth_student
@load_page(path=misc.api_sport)
async def page_sport(message, student: Student, api_data: list):
    key = types.InlineKeyboardMarkup()
    for a in api_data:
        key.add(types.InlineKeyboardButton(a['sport'], callback_data=set_callback(CallbackFuncs.SPORT_TYPE, a['sportid'])))
    await message.answer(__('page_sport', locale=student.lang), reply_markup=key)


def get_days_keyboard(s_id):
    # TODO move to utils, i18n
    days = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд')
    buttons = []
    key = types.InlineKeyboardMarkup()
    for day in range(len(days)):
        buttons.append(types.InlineKeyboardButton(days[day],
                       callback_data=set_callback(CallbackFuncs.SPORT_DAY, {'day': day, 'id': s_id})))
    key.add(*buttons[0:3])
    key.add(*buttons[3:5])
    key.add(*buttons[5:])
    return key


# noinspection PyUnusedLocal
@load_page(path=misc.api_sport)
async def get_sport_schedule(message, sport_id, student: Student, api_data: list, day=0):
    # TODO move to utils, i18n
    day_names_api_match = ("Понеділок", "Вівторок", "Середа", "Четвер", "П`ятниця", "Субота", "Неділя")
    day_names_ua = ("Понеділок", "Вівторок", "Середа", "Четвер", "П\'ятниця", "Субота", "Неділя")
    day_names_ru = ("Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье")
    day_names = None
    if student.lang == 'ua':
        day_names = day_names_ua
    elif student.lang == 'ru':
        day_names = day_names_ru
    text = f"{day_names[day]}:\n\n"
    day = day_names_api_match[day]
    for a in api_data:
        if a['day'] == day:
            text += "{time} — {prepod}\n".format(**a)
    return text


@auth_student
async def send_pdf(message, student: Student):
    url = f'{misc.api_url}{misc.api_doc}?email={student.mail}&pass={student.password}'
    await bot.send_document(message.chat.id, url)


async def change_lang(message, lang):
    changeQuery = f"UPDATE users SET lang=(%s) WHERE user_id=(%s)"
    with DatabaseConnection() as db:
        conn, cursor = db
        cursor.executemany(changeQuery, [(lang, message.chat.id)])
        conn.commit()
    text = key_type = None
    if lang == 'ua':
        text = "Обрана українська мова"
        key_type = Keyboards.UA_2
    elif lang == 'ru':
        text = "Выбран русский язык"
        key_type = Keyboards.RU_2
    await message.answer(text, reply_markup=reply_keyboard(key_type))


# noinspection PyUnusedLocal
@load_page(page=2)
async def calculate_mark(student, sem, api_data: list):
    mark100 = mark5 = credits_ = 0
    for subj in api_data:
        if not subj['oc_bol'] or not subj['credit']:
            continue
        mark100 += (int(subj['oc_bol']) * float(subj['credit']))
        credits_ += float(subj['credit'])
    if not mark100 or not credits_:
        return 0, 0
    mark100 = mark100 * 0.9 / credits_
    if mark100 >= 90:
        mark5 = 5
    elif mark100 >= 75:
        mark5 = 4
    elif mark5 >= 60:
        mark5 = 3
    return mark100, mark5


@auth_student
@load_page(page=5)
async def show_all_list(message, sem, student: Student, api_data: list, sort=False, contract=False):
    text = ''
    if contract:
        sort = True
        mark = await calculate_mark(student, sem=sem)
        if not mark:
            await message.answer(misc.req_err_msg)
            return
        main_info = await api_request(message, email=student.mail, passwd=student.password, page=1)
        if not main_info: return
        main_info = main_info[0]
        f_name = main_info['imya'] if main_info['imya'] else '-'
        m_name = main_info['otch'] if main_info['otch'] else '-'
        api_data.append({'fio': f"{main_info['fam']} {f_name[0]}. {m_name[0]}.",
                         'group': main_info['grupa'], 'sbal5': mark[1], 'sbal100': mark[0], 'studid': main_info['st_cod']})
    if sort:
        api_data = sorted(api_data, key=lambda x: float(x['sbal100']), reverse=True)
    for n, a in enumerate(api_data, 1):
        fio = a['fio']
        sbal100 = float(a['sbal100']).__round__(1)
        if int(a['studid']) == student.id:
            text += f"⭐ *{fio.lstrip()} ➖ {sbal100}*\n"
        else:
            text += f"*{n}.* {fio.lstrip()} ➖ {sbal100}\n"
    text = text.replace('`', "'")
    if not text:
        text = __('not_found', locale=student.lang)
    key = types.InlineKeyboardMarkup()
    if not sort:
        key.add(types.InlineKeyboardButton(__('rating_sort', locale=student.lang),
                                           callback_data=set_callback(CallbackFuncs.RATING_SHOW_ALL_SORT, sem)))
    await bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=key)


# noinspection PyUnusedLocal
@auth_student
@load_page(page=2)
async def send_histogram_of_page_2(message, sem, student: Student, api_data: list):
    subject = []
    score = []
    count = 0
    for n in api_data:
        if not n['oc_bol'].isdigit():
            continue
        score.append(int(n['oc_bol']))
        subject.append(n['subject'])
        count += 1
    answer = await api_request(message, email=student.mail, passwd=student.password, page=1)
    if answer is None: return
    histogram.histogram(count, score, subject, "{fam} {imya}\n{otch}".format(**answer[0]))
    with open("app/media/img.png", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


# noinspection PyUnusedLocal
@auth_student
@load_page(page=4)
async def send_histogram_of_page_4(message, sem, student: Student, api_data: list):
    subject = []
    score = []
    count = 0
    for n in api_data:
        score.append(int(float(n['credit']))) if n['credit'] else score.append(0)
        subject.append(n['subject'])
        count += 1
    histogram.histogram(count, score, subject, f"Семестр {sem}")
    with open("app/media/img.png", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


@auth_student
async def sport_select(message, callback_query, sport_id, student: Student):
    schedule = await get_sport_schedule(message, sport_id=sport_id, student=student)
    if not schedule:
        with suppress(exceptions.InvalidQueryID):
            await callback_query.answer(misc.req_err_msg, show_alert=True)
        return
    await message.answer(schedule, reply_markup=get_days_keyboard(sport_id))


@auth_student
async def sport_day(message, callback_query, data, student: Student):
    day = data.get('day')
    s_id = data.get('id')
    with suppress(exceptions.MessageNotModified):
        schedule = await get_sport_schedule(message, sport_id=s_id, student=student, day=day)
        if not schedule:
            with suppress(exceptions.InvalidQueryID):
                await callback_query.answer(misc.req_err_msg, show_alert=True)
            return
        await message.edit_text(schedule, reply_markup=get_days_keyboard(s_id))


async def search_students(message):
    student = await authentication(message)
    if not student: return False
    await SearchStudent.user.set()
    await message.answer(__('search_student', locale=student.lang))


@dp.message_handler(content_types=types.ContentTypes.ANY, state=SearchStudent)
@auth_student
async def handle_text(message: types.Message, state: FSMContext, student: Student):
    await state.finish()
    selectByIdQuery = "SELECT mail, pass FROM users WHERE user_id=(%s)"
    selectByFNQuery = "SELECT mail, pass FROM users WHERE f_name=(%s) AND l_name=(%s) GROUP BY stud_id"
    if message.forward_date:
        if not message.forward_from:
            await message.reply(__('user_hidden', locale=student.lang))
            return
        user_id = message.forward_from.id
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectByIdQuery, [user_id])
            result = cursor.fetchall()
    else:
        if not message.text:
            await message.reply(__('wrong_format', locale=student.lang))
            return
        if message.text in misc.buttons_ua_1 + misc.buttons_ua_2 + misc.buttons_ru_1 + misc.buttons_ru_2:
            await message.reply(__('wrong_format', locale=student.lang))
            return
        try:
            message.text.encode('utf-8')
        except UnicodeError:
            await message.reply(__('wrong_format', locale=student.lang))
            return
        s = message.text.replace('`', "'").split()
        if len(s) != 2:
            await message.reply(__('wrong_format', locale=student.lang))
            return
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.executemany(selectByFNQuery, [(s[0].capitalize(), s[1].capitalize())])
            result = cursor.fetchall()
    if not result:
        await message.reply(__('not_found', locale=student.lang))
        return
    for res in result:
        answer = await api_request(message, email=res[0], passwd=res[1], page=1)
        if answer is None: continue
        if not answer:
            await message.reply(__('not_found', locale=student.lang))
            continue
        main_page = __('page_1', locale=student.lang).format(**answer[0]).replace("`", "'")
        await message.reply(main_page, parse_mode='Markdown')
        await sleep(.05)


@auth_student
async def get_news(message, student: Student):
    message_id = (await message.answer(__('loading', locale=student.lang))).message_id
    news = news_parser.parse_news(student.faculty, update_last=False)
    if not news:
        await bot.edit_message_text(__('faculty_unsupported', locale=student.lang), message.chat.id, message_id)
        return
    news_str = ''
    for i, post in enumerate(news.posts, 1):
        news_str += f'*{i}.* [{esc_markdown(post.title)}]({esc_markdown(post.link)})\n'
        if i == 10: break
    await bot.edit_message_text(news_str, message.chat.id, message_id, parse_mode='Markdown')


@dp.callback_query_handler(lambda callback_query: True)
async def callback_inline(callback_query: types.CallbackQuery):
    data = get_callback(callback_query.data)
    if data is None:
        return
    func, data = data
    if func == CallbackFuncs.PAGE_1:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_1(callback_query.message)
    elif func == CallbackFuncs.PAGE_2:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_2(callback_query.message, sem=data)
    elif func == CallbackFuncs.PAGE_5:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_5(callback_query.message, sem=data)
    elif func == CallbackFuncs.PAGE_4:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_4(callback_query.message, sem=data)
    elif func == CallbackFuncs.SCHEDULE:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await page_academic_schedule(callback_query.message, week_num=data)
    elif func == CallbackFuncs.SPORT_TYPE:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await sport_select(callback_query.message, callback_query=callback_query, sport_id=data)
    elif func == CallbackFuncs.SPORT_DAY:
        await sport_day(callback_query.message, callback_query=callback_query, data=data)
    elif func == CallbackFuncs.RATING_SHOW_ALL:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await show_all_list(callback_query.message, sem=data)
    elif func == CallbackFuncs.RATING_SHOW_ALL_SORT:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await show_all_list(callback_query.message, sem=data, sort=True)
    elif func == CallbackFuncs.HISTOGRAM_2:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await send_histogram_of_page_2(callback_query.message, sem=data)
    elif func == CallbackFuncs.HISTOGRAM_4:
        await delete_message(bot.delete_message, chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await send_histogram_of_page_4(callback_query.message, sem=data)


async def on_startup(_):
    await bot.set_webhook(config.WEBHOOK_URL)
    info = await bot.get_webhook_info()
    print(f'URL: {info.url}\nPending update count: {info.pending_update_count}')


async def on_shutdown(_):
    await bot.delete_webhook()


def start_pooling():
    executor.start_polling(dp, skip_updates=True)


def start_webhook():
    executor.start_webhook(dispatcher=dp, webhook_path=config.WEBHOOK_PATH,
                           on_startup=on_startup, on_shutdown=on_shutdown,
                           host=config.WEBAPP_HOST, port=config.WEBAPP_PORT)
