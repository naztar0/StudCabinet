#!/usr/bin/env python
import json
import constants as c
import my_utils as mu
from database_connection import DatabaseConnection
from news_parser import parse_news
from asyncio import sleep
from time import time
from aiogram import Bot, utils

bot = Bot(c.token)


async def send_update_record_book(user_id, sem, data):
    ball = "{oc_short}{oc_ects} {oc_bol}".format(**data)
    str_send = f"❗ *Виставлено оцінку*\n" \
               f"📆 *Семестр:* {sem}\n" \
               f"📚 *Дисципліна:* {data['subject']}\n" \
               f"✅ *Оцінка:* {ball}".replace("`", "'")
    await mu.send_message(bot.send_message, utils, chat_id=user_id, text=str_send, parse_mode='Markdown')


async def updater_record_book():
    while True:
        selectUnmarkedQuery = "SELECT record_book.ID, record_book.subj_id, record_book.semester, users.mail, users.pass, users.user_id FROM record_book, users WHERE record_book.user_id=users.ID"
        deleteQuery = "DELETE FROM record_book WHERE ID=(%s)"
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectUnmarkedQuery)
            results = cursor.fetchall()
        for item in results:
            select_id, subj_id, semester, mail, passwd, user_id = item
            response = mu.req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page=2&semestr={semester}')
            if not response:
                continue
            rec_book = json.loads(response.text)
            if not rec_book:
                continue
            for a in rec_book:
                if int(a['subj_id']) == subj_id:
                    mark = a['oc_bol']
                    if mark:
                        await send_update_record_book(user_id, semester, a)
                        await sleep(.05)
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(deleteQuery, [select_id])
                            conn.commit()
            await sleep(0.1)
        await sleep(1200)  # 20 min


async def update_users_record_book():
    delay = 1314000  # 1/2 month
    while True:
        with open('timedelta', 'r') as f:
            t = f.read()
        if int(t) + delay > time():
            await sleep(86400)  # 1 day
            continue
        with open('timedelta', 'w') as f:
            f.write(str(int(time())))
        selectUsersQuery = "SELECT ID, mail, pass FROM users"
        existsQuery = "SELECT EXISTS (SELECT ID FROM record_book WHERE user_id=(%s) AND subj_id=(%s) AND semester=(%s))"
        insertQuery = "INSERT INTO record_book (user_id, subj_id, semester) VALUES (%s, %s, %s)"
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectUsersQuery)
            results = cursor.fetchall()
        for res in results:
            user_id, mail, passwd = res
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
                        cursor.executemany(existsQuery, [(user_id, subj_id, sem)])
                        exists = cursor.fetchone()[0]
                        if exists == 0:
                            cursor.executemany(insertQuery, [(user_id, subj_id, sem)])
                            conn.commit()


async def updater_news():
    while True:
        selectQuery = "SELECT user_id FROM users WHERE faculty=(%s)"
        for faculty in range(len(c.faculties)):
            news = parse_news(faculty)
            if not news:
                continue
            str_send = f'❗ *Опубліковано новину кафедри*\n' \
                       f'[{mu.esc_markdown(news[0].title)}]({mu.esc_markdown(news[0].link)})'
            with DatabaseConnection() as db:
                conn, cursor = db
                cursor.execute(selectQuery, [c.faculties[faculty]])
                results = cursor.fetchall()
            for res in results:
                await mu.send_message(bot.send_message, utils, chat_id=res[0], text=str_send, parse_mode='Markdown')
                await sleep(.05)
        await sleep(3600)  # 60 min
