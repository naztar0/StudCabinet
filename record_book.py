#!/usr/bin/env python
import json
import constants as c
from database_connection import DatabaseConnection
from my_utils import send_message, req_post
from asyncio import sleep
from time import time
from aiogram import Bot, utils

bot = Bot(c.token)


async def send_update(user_id, sem, data):
    ball = "{oc_short}{oc_ects} {oc_bol}".format(**data)
    str_send = f"❗ *Виставлено оцінку*\n" \
               f"📆 *Семестр:* {sem}\n" \
               f"📚 *Дисципліна:* {data['subject']}\n" \
               f"✅ *Оцінка:* {ball}"
    await send_message(bot.send_message, utils, chat_id=user_id, text=str_send.replace("`", "'"))
    print(user_id, str_send)  # TODO: just for test, remove in future


async def updater():
    while True:
        selectUnmarkedQuery = "SELECT record_book.ID, record_book.subj_id, record_book.semester, users.mail, users.pass, users.user_id FROM record_book, users WHERE record_book.user_id=users.ID"
        deleteQuery = "DELETE FROM record_book WHERE ID=(%s)"
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectUnmarkedQuery)
            results = cursor.fetchall()
        for item in results:
            select_id, subj_id, semester, mail, passwd, user_id = item
            response = req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page=2&semestr={semester}')
            if not response:
                continue
            rec_book = json.loads(response.text)
            if not rec_book:
                continue
            for a in rec_book:
                if int(a['subj_id']) == subj_id:
                    mark = a['oc_bol']
                    if mark:
                        await send_update(user_id, semester, a)
                        await sleep(.05)
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(deleteQuery, [select_id])
                            conn.commit()
            await sleep(0.1)
        await sleep(10800)  # 3 hrs


async def update_users():
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
                response = req_post(f'https://schedule.kpi.kharkov.ua/json/kabinet?email={mail}&pass={passwd}&page=2&semestr={sem}')
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
