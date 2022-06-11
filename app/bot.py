#!/usr/bin/env python
import logging
from asyncio import sleep
from contextlib import suppress
from app import config, misc
from app.misc import bot, dp, temp_dir
from app.utils.my_utils import *
from app.utils import histogram
from app.utils.database_connection import DatabaseConnection

from aiogram import executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import exceptions


class Form(StatesGroup): authorization = State()
class Feedback(StatesGroup): text = State()
class SendMessageToUsers(StatesGroup): text = State()
class SendMessageToUser(StatesGroup): text = State()
class SearchStudent(StatesGroup): user = State()


@dp.message_handler(commands=['start'])
async def handle_text(message: types.Message):
    await reg_key(message)


@dp.message_handler(commands=['feedback'])
async def handle_text(message: types.Message):
    student = await authentication(message, skip=True)
    await message.reply(student.text('feedback_start'))
    await Feedback.text.set()


@dp.message_handler(content_types=[types.ContentType.ANY], state=Feedback.text)
async def feedback(message: types.Message, state: FSMContext):
    await state.finish()
    student = await authentication(message, skip=True)
    if message.text:
        for exception in ['/exit', misc.sign_in_butt], misc.buttons_ua_1, misc.buttons_ru_1:
            if message.text in exception:
                await message.reply(student.text('cancel'))
                return
    name = esc_md(message.from_user.full_name)
    username = esc_md(message.from_user.username)
    text = f"*Feedback!\n\nUser:* [{name}](tg://user?id={message.from_user.id})\n" \
           f"*UserName:* @{username}\n*ID:* {message.from_user.id}"
    await bot.send_message(config.BOT_ADMIN, text, parse_mode="Markdown")
    await bot.forward_message(config.BOT_ADMIN, message.chat.id, message.message_id)
    await message.answer(student.text('feedback_finish'))


@dp.message_handler(commands=['reply'])
async def handle_text(message: types.Message):
    if message.chat.id == config.BOT_ADMIN:
        await message.answer("Введите 'user_id сообщение' для отправки пользователю (Markdown)\n\nОтмена - [/exit]")
        await SendMessageToUser.text.set()


@dp.message_handler(content_types=['text'], state=SendMessageToUser.text)
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
    data = message.text.split(maxsplit=1)
    if not data[0].isdigit() or len(data) != 2:
        await message.answer("Неверный формат user_id!")
        return
    if await send_message(bot.send_message, chat_id=int(data[0]), text=data[1], parse_mode='Markdown'):
        await message.answer('Отправлено')
    else:
        await message.answer('Не отправлено')


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
    with open(temp_dir/'posting.txt', 'w') as f:
        f.write(message.text)


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
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
    elif message.text == misc.buttons_en_2[4]:
        await message.answer(misc.helper_en, parse_mode="Markdown", disable_web_page_preview=True)
    elif message.text in (misc.buttons_ua_1[0], misc.buttons_ru_1[0], misc.buttons_en_1[0]):
        await page_1(message)
    elif message.text in (misc.buttons_ua_1[1], misc.buttons_ru_1[1], misc.buttons_en_1[1]):
        await choose_from_inline(message, misc.sem_name, generate_inline_keyboard(CallbackFuncs.PAGE_2, 12))
    elif message.text in (misc.buttons_ua_1[2], misc.buttons_ru_1[2], misc.buttons_en_1[2]):
        await choose_from_inline(message, misc.sem_name, generate_inline_keyboard(CallbackFuncs.PAGE_5, 12))
    elif message.text in (misc.buttons_ua_1[6], misc.buttons_ru_1[6], misc.buttons_en_1[6]):
        await choose_from_inline(message, misc.sem_name, generate_inline_keyboard(CallbackFuncs.PAGE_4, 12))
    elif message.text in (misc.buttons_ua_1[4], misc.buttons_ru_1[4], misc.buttons_en_1[4]):
        await choose_from_inline(message, misc.week_name, generate_inline_keyboard(CallbackFuncs.SCHEDULE, 2))
    elif message.text in (misc.buttons_ua_1[3], misc.buttons_ru_1[3], misc.buttons_en_1[3]):
        await page_3(message)
    elif message.text in (misc.buttons_ua_1[5], misc.buttons_ru_1[5], misc.buttons_en_1[5]):
        await page_sport(message)
    elif message.text in (misc.buttons_ua_2[0], misc.buttons_ru_2[0], misc.buttons_en_2[0]):
        await page_6(message)
    elif message.text in (misc.buttons_ua_2[1], misc.buttons_ru_2[1], misc.buttons_en_2[1]):
        await send_pdf(message)
    elif message.text == misc.buttons_ua_2[5]:
        await change_lang(message, 'ru')
    elif message.text == misc.buttons_ru_2[5]:
        await change_lang(message, 'en')
    elif message.text == misc.buttons_en_2[5]:
        await change_lang(message, 'ua')
    elif message.text == misc.buttons_ua_1[7]:
        await message.answer(misc.buttons_ua_1[7], reply_markup=reply_keyboard(Keyboards.UA_2))
    elif message.text == misc.buttons_ru_1[7]:
        await message.answer(misc.buttons_ru_1[7], reply_markup=reply_keyboard(Keyboards.RU_2))
    elif message.text == misc.buttons_en_1[7]:
        await message.answer(misc.buttons_en_1[7], reply_markup=reply_keyboard(Keyboards.EN_2))
    elif message.text == misc.buttons_ua_2[6]:
        await message.answer(misc.buttons_ua_2[6], reply_markup=reply_keyboard(Keyboards.UA_1))
    elif message.text == misc.buttons_ru_2[6]:
        await message.answer(misc.buttons_ru_2[6], reply_markup=reply_keyboard(Keyboards.RU_1))
    elif message.text == misc.buttons_en_2[6]:
        await message.answer(misc.buttons_en_2[6], reply_markup=reply_keyboard(Keyboards.EN_1))
    elif message.text in (misc.buttons_ua_2[2], misc.buttons_ru_2[2], misc.buttons_en_2[2]):
        await search_students(message)
    elif message.text in (misc.buttons_ua_2[3], misc.buttons_ru_2[3], misc.buttons_en_2[3]):
        await get_news(message)


@dp.message_handler(content_types=['text'], state=Form.authorization)
async def registration(message: types.Message, state: FSMContext):
    await state.finish()
    s = message.text.split()
    if len(s) != 2:
        await message.answer("Невірний формат")
        return
    mail, passwd = s
    answer = await api_request(message, {'email': mail, 'pass': passwd, 'page': 1})
    if answer is None: return
    if not answer:
        await message.answer("Невірний email або пароль")
        return
    student_id = answer[0]['st_cod']
    group_id = answer[0]['gid']
    f_name = answer[0]['imya'].replace('`', "'")
    l_name = answer[0]['fam'].replace('`', "'")
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
        rec_book = await api_request(message, {'email': mail, 'pass': passwd, 'page': 2, 'semestr': sem})
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
async def choose_from_inline(message, names, reply_markup, student: Student):
    await message.answer(names[student.lang], reply_markup=reply_markup)


@auth_student
@load_page(mandatory=True, page=1)
async def page_1(message, student: Student, api_data):
    if not api_data:
        await message.answer(misc.auth_err_msg)
        await message.answer(misc.greetings_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())
        await Form.authorization.set()
        return
    main_page = student.text('page_1').format(**esc_md(api_data[0]))
    await message.answer(main_page, parse_mode="Markdown")


@auth_student
@load_page(page=2)
async def page_2(message, sem, student: Student, api_data: list):
    with_mark = len(api_data)
    subjects = ''
    for a in api_data:
        control = student.text('page_2_exam')
        if a['control'] == "З": control = student.text('page_2_zach')
        hvost = a['if_hvost']
        if not hvost: hvost = "—"
        ball = "{oc_short}{oc_ects} {oc_bol}".format(**a)
        if ball == " ":
            ball = "—"
            with_mark -= 1
        subjects += student.text('page_2').format(*esc_md([a['subject'], ball, control, a['credit'], hvost]))

    key_histogram = None
    if with_mark > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(student.text('histogram'),
                                                     callback_data=set_callback(CallbackFuncs.HISTOGRAM_2, sem)))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


@auth_student
@load_page(page=5)
async def page_5(message, sem, student: Student, api_data: list):
    all_in_list = len(api_data)
    for a in api_data:
        if int(a['studid']) == student.id:
            rang1 = student.text('page_5').format(a['n'], all_in_list, a['sbal100'], a['sbal5'])
            num = int(a['n'])
            break
    else:
        await show_all_list(message, sem=sem, contract=True)
        return
    percent = float(num * 100 / all_in_list).__round__(2)
    percent_str = student.text('page_5_rate').format(percent)
    stip = student.text('page_5_stp')
    if percent < 50:
        if percent < 45:
            if percent < 40:
                stip += "100 %"
            else: stip += student.text('page_5_probability_high')
        else: stip += student.text('page_5_probability_low')
    else: stip += student.text('page_5_probability_zero')

    ps = student.text('page_5_ps')
    key_extend = types.InlineKeyboardMarkup()
    key_extend.add(types.InlineKeyboardButton(student.text('page_5_all_list'),
                                              callback_data=set_callback(CallbackFuncs.RATING_SHOW_ALL, sem)))
    await message.answer(rang1 + percent_str + stip + ps, parse_mode="Markdown", reply_markup=key_extend)


@auth_student
@load_page(page=4)
async def page_4(message, sem, student: Student, api_data: list):
    subjects = student.text('page_4_head').format(**api_data[0])
    for i, a in enumerate(api_data):
        control = student.text('page_2_exam')
        if a['control'] == "З": control = student.text('page_2_zach')
        subjects += student.text('page_4').format(i + 1, *esc_md([a['subject'], a['audit'], a['credit']]), control)

    key_histogram = None
    if len(api_data) > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton(student.text('histogram'),
                                                     callback_data=set_callback(CallbackFuncs.HISTOGRAM_4, sem)))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


@auth_student
@load_page(page=3)
async def page_3(message, student: Student, api_data: list):
    subjects = ''
    for a in api_data:
        subjects += student.text('page_3').format(*esc_md([a['subject'], a['prepod'], a['data']]))
    await message.answer(subjects, parse_mode="Markdown")


@auth_student
@load_page(page=6)
async def page_6(message, student: Student, api_data: list):
    subjects = student.text('page_6_header').format(api_data[0]['dog_name'], api_data[0]['start_date'], api_data[0]['dog_price'])
    for a in api_data:
        subjects += student.text('page_6').format(*esc_md([a['term_start'], a['paid_date'], a['paid_value'], a['dp_id']]))
    await message.answer(subjects, parse_mode="Markdown")


@auth_student
async def page_academic_schedule(message, week_num, student: Student):
    week = '' if week_num == 1 else '2'
    api_data = await api_request(message, url=f'{misc.api_sched}{week}/{student.group_id}')
    if api_data is None: return
    if not api_data:
        await message.answer(student.text('not_found'))
        return
    week_name = misc.week_name[student.lang]
    day_names = misc.day_names[student.lang]
    subjects = f"📆 *{week_name} {week_num}*\n\n"
    days_sub = api_data['Monday'], api_data['Tuesday'], api_data['Wednesday'], api_data['Thursday'], api_data['Friday']
    for i, day in enumerate(days_sub):
        subjects += f"*📌 {day_names[i]}*\n"
        for j, p_num in enumerate(misc.para_num):
            para_json = day[misc.para_name[j]]
            if para_json['Name']:
                name = esc_md(para_json['Name'])
                prepod = esc_md(para_json['Prepod'])
                para_data = f"*{name}* _{para_json['vid']}_\n➖ {para_json['Aud']} _({prepod})_"
                subjects += f"{p_num} {para_data}\n"
        subjects += "➖➖➖➖➖➖➖➖➖➖➖➖\n"
    await message.answer(subjects, parse_mode='Markdown')


@auth_student
@load_page(path=misc.api_sport)
async def page_sport(message, student: Student, api_data: list):
    key = types.InlineKeyboardMarkup()
    for a in api_data:
        key.add(types.InlineKeyboardButton(a['sport'], callback_data=set_callback(CallbackFuncs.SPORT_TYPE, a['sportid'])))
    await message.answer(student.text('page_sport'), reply_markup=key)


def get_days_keyboard(sport_id, locale):
    days = misc.day_short_names[locale]
    buttons = []
    key = types.InlineKeyboardMarkup()
    for day in range(len(days)):
        buttons.append(types.InlineKeyboardButton(days[day],
                       callback_data=set_callback(CallbackFuncs.SPORT_DAY, {'day': day, 'id': sport_id})))
    key.add(*buttons[0:3])
    key.add(*buttons[3:5])
    key.add(*buttons[5:])
    return key


# noinspection PyUnusedLocal
@load_page(path=misc.api_sport)
async def get_sport_schedule(message, sport_id, student: Student, api_data: list, day=0):
    day_names = misc.day_names[student.lang]
    text = f"{day_names[day]}:\n\n"
    day = misc.day_names_api_match[day]
    for a in api_data:
        if a['day'] == day:
            text += "{time} — {prepod}\n".format(**a)
    return text


@auth_student
async def send_pdf(message, student: Student):
    url = f'{misc.api_doc}?email={student.mail}&pass={student.password}'
    try:
        await bot.send_document(message.chat.id, url)
    except (exceptions.WrongFileIdentifier, exceptions.InvalidHTTPUrlContent):
        await message.answer(student.text('not_found'))


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
    elif lang == 'en':
        text = "English selected"
        key_type = Keyboards.EN_2
    await message.answer(text, reply_markup=reply_keyboard(key_type))


# noinspection PyUnusedLocal
@load_page(page=2)
async def calculate_mark(message, student, sem, api_data: list):
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
        mark = await calculate_mark(message, student=student, sem=sem)
        if not mark:
            await message.answer(misc.req_err_msg)
            return
        main_info = await api_request(message, {'email': student.mail, 'pass': student.password, 'page': 1})
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
            text += f"⭐ *{esc_md(fio.lstrip())} ➖ {sbal100}*\n"
        else:
            text += f"*{n}.* {esc_md(fio.lstrip())} ➖ {sbal100}\n"
    if not text:
        text = student.text('not_found')
    key = types.InlineKeyboardMarkup()
    if not sort:
        key.add(types.InlineKeyboardButton(student.text('rating_sort'),
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
    answer = await api_request(message, {'email': student.mail, 'pass': student.password, 'page': 1})
    if answer is None: return
    histogram.histogram(count, score, subject, "{fam} {imya}\n{otch}".format(**answer[0]))
    with open("app/media/img.png", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


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
    histogram.histogram(count, score, subject, f"{misc.sem_name[student.lang]} {sem}")
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
    await message.answer(schedule, reply_markup=get_days_keyboard(sport_id, student.lang))


@auth_student
async def sport_day(message, callback_query, data, student: Student):
    day = data.get('day')
    sport_id = data.get('id')
    with suppress(exceptions.MessageNotModified):
        schedule = await get_sport_schedule(message, sport_id=sport_id, student=student, day=day)
        if not schedule:
            with suppress(exceptions.InvalidQueryID):
                await callback_query.answer(misc.req_err_msg, show_alert=True)
            return
        await message.edit_text(schedule, reply_markup=get_days_keyboard(sport_id, student.lang))


async def search_students(message):
    student = await authentication(message)
    if not student: return False
    await SearchStudent.user.set()
    await message.answer(student.text('search_student'))


@dp.message_handler(content_types=types.ContentTypes.ANY, state=SearchStudent)
@auth_student
async def handle_text(message: types.Message, state: FSMContext, student: Student):
    await state.finish()
    selectByIdQuery = "SELECT mail, pass FROM users WHERE user_id=(%s)"
    selectByFNQuery = "SELECT mail, pass FROM users WHERE f_name=(%s) AND l_name=(%s) GROUP BY stud_id"
    if message.forward_date:
        if not message.forward_from:
            await message.reply(student.text('user_hidden'))
            return
        user_id = message.forward_from.id
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectByIdQuery, [user_id])
            result = cursor.fetchall()
    else:
        if not message.text:
            await message.reply(student.text('wrong_format'))
            return
        if message.text in misc.buttons_ua_1 + misc.buttons_ua_2 + misc.buttons_ru_1 + misc.buttons_ru_2:
            await message.reply(student.text('wrong_format'))
            return
        try:
            message.text.encode('utf-8')
        except UnicodeError:
            await message.reply(student.text('wrong_format'))
            return
        s = esc_md(message.text).split()
        if len(s) != 2:
            await message.reply(student.text('wrong_format'))
            return
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.executemany(selectByFNQuery, [(s[0].capitalize(), s[1].capitalize())])
            result = cursor.fetchall()
    if not result:
        await message.reply(student.text('not_found'))
        return
    for res in result:
        answer = await api_request(message, {'email': res[0], 'pass': res[1], 'page': 1})
        if answer is None: continue
        if not answer:
            await message.reply(student.text('not_found'))
            continue
        main_page = student.text('page_1').format(**esc_md(answer[0]))
        await message.reply(main_page, parse_mode='Markdown')
        await sleep(.05)


@auth_student
async def get_news(message, student: Student):
    news = get_update_json(temp_dir/'news_texts.json', student.faculty)
    if not news:
        await message.answer(student.text('faculty_unsupported'))
        return
    await message.answer(news, parse_mode='Markdown')


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
    logging.warning(f'URL: {info.url}\nPending update count: {info.pending_update_count}')


async def on_shutdown(_):
    await bot.delete_webhook()


def start_pooling():
    executor.start_polling(dp, skip_updates=True)


def start_webhook():
    executor.start_webhook(dispatcher=dp, webhook_path=config.WEBHOOK_PATH,
                           on_startup=on_startup, on_shutdown=on_shutdown,
                           host=config.WEBAPP_HOST, port=config.WEBAPP_PORT,
                           skip_updates=True, print=logging.warning)
