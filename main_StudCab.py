#!/usr/bin/env python
import requests
import json
import constants as c
import mysql.connector

from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import histogram

bot = Bot(c.token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup): authorization = State()


class Feedback(StatesGroup): text = State()


class SendMessageToUsers(StatesGroup): text = State()


button = ["ℹ Общая иформация", "📕 Зачётная книжка", "📊 Рейтинг", "⚠ Долги", "🗓 Учебный план", "📆 Расписание спорт. каф.", "❓Помощь"]


def keyboard():
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    but_1 = types.KeyboardButton(button[0])
    but_2 = types.KeyboardButton(button[1])
    but_3 = types.KeyboardButton(button[2])
    but_4 = types.KeyboardButton(button[3])
    but_5 = types.KeyboardButton(button[4])
    but_6 = types.KeyboardButton(button[5])
    but_7 = types.KeyboardButton(button[6])
    key.add(but_1, but_2)
    key.add(but_3, but_4)
    key.add(but_5, but_6)
    key.add(but_7)
    return key


@dp.message_handler(commands=['start'])
async def handle_text(message: types.Message):
    await reg_key(message)


async def reg_key(message):
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    but_1 = types.KeyboardButton("👥 Войти в кабинет")
    but_2 = types.KeyboardButton(button[6])
    key.add(but_1)
    key.add(but_2)
    await message.answer("Чтобы продолжить нажмите на одну из кнопок", reply_markup=key)


@dp.message_handler(commands=['keyboard'])
async def handle_text(message: types.Message):
    await message.answer("Клавиатура включена", reply_markup=keyboard())


@dp.message_handler(commands=['feedback'])
async def handle_text(message: types.Message):
    await message.reply("Напишите сообщение с пожеланиями или вопросами касательно бота\n\nОтмена - [/exit]")
    await Feedback.text.set()


@dp.message_handler(state=Feedback.text)
async def feedback(message: types.Message, state: FSMContext):
    await state.finish()
    m = str(message.text).replace('_', '\\_').replace('*', '\\*').replace('`', '\\`').replace('[', '\\[')
    if m in {"/exit", "👥 Войти в кабинет", button[0], button[1],
             button[2], button[3], button[4], button[5], button[6]}:
        await message.reply("Отменено")
        return
    text = f"*Feedback!\n\nUser:* [{message.from_user.full_name}](tg://user?id={message.from_user.id})\n\n{m}"
    await bot.send_message(c.admin, text, parse_mode="Markdown")
    await message.answer("Ваше сообщение отправлено")


@dp.message_handler(commands=['send'])
async def handle_text(message: types.Message):
    if message.chat.id == c.admin:
        await message.answer("Введите сообщение для отправки пользователям\n\nОтмена - [/exit]")
        await SendMessageToUsers.text.set()


@dp.message_handler(content_types=['text'], state=SendMessageToUsers.text)
async def handle_text(message: types.Message, state: FSMContext):
    await state.finish()
    if message.text == "/exit":
        await message.answer("Отменено")
        return
    conn = mysql.connector.connect(host=c.host, user=c.user, passwd=c.password, database=c.db)
    cursor = conn.cursor(buffered=True)
    selectQuery = "SELECT user_id FROM users"
    cursor.execute(selectQuery)
    users = cursor.fetchall()
    conn.close()
    i = 0
    j = 0
    for user in users:
        try:
            await bot.send_message(user[0], message.text)
            i += 1
        except utils.exceptions.BotBlocked: j += 1
    await message.answer(f"Отправлено: {i}\nНе отправлено: {j}")


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    if message.text == "👥 Войти в кабинет":
        auth = await authentication(message, first=True)
        if auth:
            return
        await message.answer("Введите свой Email и пароль от личного кабинета через пробел\nНапример:\nemail@example.com d1v8s3")
        await Form.authorization.set()
    elif message.text == button[6]:
        await message.answer(c.helper)
    elif message.text == button[0]:
        data = await page_1(message)
        if not data:
            return
        await message.answer(str(data), parse_mode="Markdown")
    elif message.text == button[1]:
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
        await message.answer("Выберите семестр", reply_markup=key)
    elif message.text == button[2]:
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
        await message.answer("Выберите семестр", reply_markup=key)
    elif message.text == button[4]:
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
        await message.answer("Выберите семестр", reply_markup=key)
    elif message.text == button[3]:
        await page_3(message)
    elif message.text == button[5]:
        await page_sport(message)
    elif message.text == "/pdf":
        await send_pdf(message)


async def authentication(message, first=False):
    conn = mysql.connector.connect(host=c.host, user=c.user, passwd=c.password, database=c.db)
    cursor = conn.cursor(buffered=True)
    findQuery = "SELECT mail, pass, stud_id FROM users WHERE user_id=(%s)"
    cursor.execute(findQuery, [message.chat.id])
    auth = cursor.fetchone()
    conn.close()
    if first:
        if auth:
            await message.answer("Похоже, Вы уже входили в свой кабинет", reply_markup=keyboard())
    else:
        if not auth:
            await message.answer("Ошибка аутентификации, повторите попытку входа")
            await reg_key(message)
    return auth


@dp.message_handler(content_types=['text'], state=Form.authorization)
async def registration(message: types.Message, state: FSMContext):
    s = message.text
    await state.finish()
    try:
        mail = s.split(" ")[0]
        passwd = s.split(" ")[1]
    except IndexError:
        await message.answer("Неверный ввод")
        return
    page = "1"
    response_1 = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    answer_1 = json.loads(response_1.text)
    if not answer_1:
        await message.answer("Неправильный email или пароль")
        return
    student_id = "{st_cod}".format(**answer_1[0])
    conn = mysql.connector.connect(host=c.host, user=c.user, passwd=c.password, database=c.db)
    cursor = conn.cursor(buffered=True)
    inputQuery = "INSERT INTO users (user_id, stud_id, mail, pass) VALUES (%s, %s, %s, %s)"
    cursor.executemany(inputQuery, [(message.chat.id, student_id, mail, passwd)])
    conn.commit()
    conn.close()
    await message.answer("Вход успешно выполнен!", reply_markup=keyboard())


async def page_1(message):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "1"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    answer = json.loads(response.text)[0]
    main_page = "👤 *ФИО:* {fam} {imya} {otch}\n\n" \
                "🔢 *Курс:* {kurs}\n\n" \
                "👥 *Група:* {grupa}\n\n" \
                "🏢 *Факультет:* {fakultet}\n\n" \
                "👨‍🏫 *Кафедра:* {kafedra}\n\n" \
                "🔴 *Специализация:* {specialization}\n\n" \
                "🔵 *Специальность:* {speciality}\n\n" \
                "🟢 *Образовательная программа:* {osvitprog}\n\n" \
                "👨‍🎓 *Уровень обучения:* {train_level}\n\n" \
                "🛄 *Форма обучения:* {train_form}\n\n" \
                "💵 *Оплата:* {oplata}\n\n" \
                "📄 *Семестровый план:* \\[/pdf]".format(**answer).replace("`", "'")
    return main_page


async def page_2(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "2"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    answer = json.loads(response.text)
    if not answer:
        await message.answer("Не найдено")
        return
    with_mark = len(answer)
    subjects = ""
    for a in answer:
        ez = "Экзамен"
        if "{control}".format(**a) == "З": ez = "Зачёт"
        hvost = "{if_hvost}".format(**a)
        if not hvost: hvost = "—"
        ball = "{oc_short}{oc_ects} {oc_bol}".format(**a)
        if ball == " ":
            ball = "—"
            with_mark -= 1

        subjects = subjects + "📚 *Дисциплина:* {subject}\n\n" \
                              f"✅ *Оценка:* {ball}\n\n" \
                              f"📝 *Е/З:* {ez}\n\n" \
                              "📊 *Кредит:* {credit}\n\n" \
                              f"❗ *Хвост:* {hvost}\n➖➖➖➖➖➖➖➖➖➖➖➖\n\n"\
                              .format(**a).replace("`", "'")

    key_histogram = None
    if with_mark > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton("Гистограмма", callback_data="histogram2" + sem))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


async def page_5(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    student_id = auth[2]
    page = "5"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    answer = json.loads(response.text)
    all_in_list = len(answer)
    for a in answer:
        if int("{studid}".format(**a)) == student_id:
            rang1 = "📊 *Рейтинговый номер:* {n} из " \
                    f"{all_in_list}\n\n" \
                    "✅ *Рейтинговый балл:* {sbal100} | {sbal5}\n\n".format(**a)
            num = int("{n}".format(**a))
            break
    else:
        await message.answer("Не найдено")
        return
    percent = float("%.2f" % (num * 100 / all_in_list))
    percent_str = "📈 *Процент в рейтинге:* {} %\n\n".format(percent)
    stip = "💸 *Вероятность получения стипендии:* "
    if percent < 50:
        if percent < 45:
            if percent < 40:
                stip += "100 %"
            else: stip += "высокая"
        else: stip += "низкая"
    else: stip += "нулевая"

    ps = "\n\n_PS: если не выставлены оценки по всем дисциплинам, то рейтинг не является достоверным_"
    key_extend = types.InlineKeyboardMarkup()
    key_extend.add(types.InlineKeyboardButton("Показать весь список", callback_data="all_list" + sem))
    await message.answer(rang1 + percent_str + stip + ps, parse_mode="Markdown", reply_markup=key_extend)


async def page_4(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "4"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    answer = json.loads(response.text)
    if not answer:
        await message.answer("Не найдено")
        return
    i = 0
    subjects = "*Курс {kurs}, семестр {semestr}:*\n\n".format(**answer[0])
    for a in answer:
        subjects = subjects + "`" + str(i + 1) + ".` " + "*Дисциплина:* {subject}\n" \
                              "⏱ *Аудиторных часов:* {audit}\n" \
                              "📊 *Кредит:* {credit}\n➖➖➖➖➖➖➖➖➖➖➖➖\n" \
                              .format(**a).replace("`", "'")
        i += 1

    key_histogram = None
    if len(answer) > 4:
        key_histogram = types.InlineKeyboardMarkup()
        key_histogram.add(types.InlineKeyboardButton("Гистограмма", callback_data="histogram4" + sem))
    await message.answer(subjects, parse_mode="Markdown", reply_markup=key_histogram)


async def page_3(message):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "3"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}')
    answer = json.loads(response.text)
    if not answer:
        await message.answer("Не найдено")
        return
    subjects = ""
    for a in answer:
        subjects = subjects + "📚 *Дисциплина:* {subject}\n\n" \
                              "👨‍🏫 *Препод:* {prepod}\n\n" \
                              "📅 *Дата:* {data}\n➖➖➖➖➖➖➖➖➖➖➖➖\n\n" \
                              .format(**a).replace("`", "'")
    await message.answer(subjects, parse_mode="Markdown")


async def page_sport(message):
    response = requests.post('https://schedule.kpi.kharkov.ua/json/sport')
    answer = json.loads(response.text)
    if not answer:
        await message.answer("Не найдено")
        return
    key = types.InlineKeyboardMarkup()
    for a in answer:
        key.add(types.InlineKeyboardButton("{sport}".format(**a), callback_data="s{sportid}".format(**a)))
    await message.answer("Выберите вид спорта", reply_markup=key)


def days(s_id):
    key = types.InlineKeyboardMarkup()
    but_1 = types.InlineKeyboardButton("Пн", callback_data=f"day1{s_id}")
    but_2 = types.InlineKeyboardButton("Вт", callback_data=f"day2{s_id}")
    but_3 = types.InlineKeyboardButton("Ср", callback_data=f"day3{s_id}")
    but_4 = types.InlineKeyboardButton("Чт", callback_data=f"day4{s_id}")
    but_5 = types.InlineKeyboardButton("Пт", callback_data=f"day5{s_id}")
    but_6 = types.InlineKeyboardButton("Сб", callback_data=f"day6{s_id}")
    but_7 = types.InlineKeyboardButton("Вс", callback_data=f"day7{s_id}")
    key.add(but_1, but_2, but_3)
    key.add(but_4, but_5)
    key.add(but_6, but_7)
    return key


def get_schedule(s_id, day):
    day_names = ["", "Понеділок", "Вівторок", "Середа", "Четвер", "П`ятниця", "Субота", "Неділя"]
    day = day_names[day]
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/sport?sport_id={s_id}')
    answer = json.loads(response.text)
    text = f"{day}:\n\n"
    for a in answer:
        if "{day}".format(**a) == day:
            text += "{time} — {prepod}\n".format(**a)
    return text


async def send_pdf(message):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    url = f'http://schedule.kpi.kharkov.ua/json/getpdf?email={mail}&pass={passwd}'
    await bot.send_document(message.chat.id, url)


async def show_all_list(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    student_id = auth[2]
    page = "5"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    answer = json.loads(response.text)
    text = ""
    for a in answer:
        n = "{n}".format(**a)
        fio = "{fio}".format(**a)
        sbal100 = "%.1f" % float("{sbal100}".format(**a))
        if int("{studid}".format(**a)) == student_id:
            text += f"⭐ *{fio} ➖ {sbal100}*\n"
        else:
            text += f"*{n}.* {fio} ➖ {sbal100}\n"
    text = text.replace('`', "'")
    await bot.send_message(message.chat.id, text, parse_mode="Markdown")


async def send_histogram_of_page_2(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "2"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    answer = json.loads(response.text)
    subject = []
    score = []
    count = 0
    for n in answer:
        if not "{oc_bol}".format(**n).isdigit():
            continue
        score.append(int("{oc_bol}".format(**n)))
        subject.append("{subject}".format(**n))
        count += 1
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page=1')
    answer = json.loads(response.text)[0]
    histogram.histogram(count, score, subject, "{fam} {imya}\n{otch}".format(**answer))
    with open("media/img.jpg", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


async def send_histogram_of_page_4(message, sem):
    auth = await authentication(message)
    if not auth: return False
    mail = auth[0]
    passwd = auth[1]
    page = "4"
    response = requests.post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page={page}&semestr={sem}')
    answer = json.loads(response.text)
    subject = []
    score = []
    count = 0
    for n in answer:
        score.append(int(float("{credit}".format(**n))))
        subject.append("{subject}".format(**n))
        count += 1
    histogram.histogram(count, score, subject, f"Семестр {sem}")
    with open("media/img.jpg", "rb") as f:
        img = f.read()
    await bot.send_photo(message.chat.id, img)


@dp.callback_query_handler(lambda callback_query: True)
async def callback_inline(callback_query: types.CallbackQuery):
    data = str(callback_query.data)
    if data[0] == "1":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await page_1(callback_query.message)
    elif data[0] == "2":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await page_2(callback_query.message, data[1:])
    elif data[0] == "3":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await page_5(callback_query.message, data[1:])
    elif data[0] == "4":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        await page_4(callback_query.message, data[1:])

    elif data[0] == "s":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        s_id = data[1:]
        response = requests.post(f'https://schedule.kpi.kharkov.ua/json/sport?sport_id={s_id}')
        answer = json.loads(response.text)
        if not answer:
            await callback_query.answer("Не найдено", show_alert=True)
            return
        await bot.send_message(callback_query.from_user.id, get_schedule(s_id, 1), reply_markup=days(s_id))

    elif data[:3] == "day":
        day = int(data[1])
        s_id = data[4:]
        try:
            await bot.edit_message_text(get_schedule(s_id, day), callback_query.from_user.id,
                                        callback_query.message.message_id, callback_query.from_user.id, reply_markup=days(s_id))
        except utils.exceptions.MessageNotModified:
            await callback_query.answer("Выбран тот же день!")

    elif data[:8] == "all_list":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        sem = data[8:]
        await show_all_list(callback_query.message, sem)

    elif data[:10] == "histogram2":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        sem = data[10:]
        await send_histogram_of_page_2(callback_query.message, sem)

    elif data[:10] == "histogram4":
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        sem = data[10:]
        await send_histogram_of_page_4(callback_query.message, sem)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
