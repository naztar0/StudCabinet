#!/usr/bin/env python
import json
import app.utils.my_utils as mu
from app.misc import bot, faculties, temp_dir, api_url_v2
from app.config import BOT_ADMIN
from app.utils.database_connection import DatabaseConnection
from app.utils.news_parser import parse_news
from asyncio import sleep
from time import time
from os import path, remove


async def _send_update_record_book(user_id, sem, data):
    ball = "{oc_short}{oc_ects} {oc_bol}".format(**data)
    str_send = f"❗ *Виставлено оцінку*\n" \
               f"📆 *Семестр:* {sem}\n" \
               f"📚 *Дисципліна:* {data['subject']}\n" \
               f"✅ *Оцінка:* {ball}".replace("`", "'")
    await mu.send_message(bot.send_message, chat_id=user_id, text=str_send, parse_mode='Markdown')


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
            response = mu.req_post(api_url_v2, json={'email': mail, 'pass': passwd, 'page': 2, 'semester': semester})
            if not response:
                continue
            rec_book = json.loads(response.text)
            if not rec_book:
                continue
            for a in rec_book:
                if not a['oc_id']:
                    continue
                if a['oc_id'] == subj_id:
                    mark = a['oc_bol']
                    if mark:
                        await _send_update_record_book(user_id, semester, a)
                        await sleep(.05)
                        with DatabaseConnection() as db:
                            conn, cursor = db
                            cursor.execute(deleteQuery, [select_id])
                            conn.commit()
            await sleep(0.1)
        await sleep(1200)  # 20 min


async def update_users_record_book():
    delay = 1314000  # 1/2 month
    filename = temp_dir/'timedelta'
    while True:
        with open(filename, 'r') as f:
            t = f.read()
        if int(t) + delay > time():
            await sleep(86400)  # 1 day
            continue
        with open(filename, 'w') as f:
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
                response = mu.req_post(api_url_v2, json={'email': mail, 'pass': passwd, 'page': 2, 'semester': sem})
                if not response:
                    continue
                rec_book = json.loads(response.text)
                if not rec_book:
                    break
                for a in rec_book:
                    mark = a['oc_bol']
                    if mark or not a['oc_id']:
                        continue
                    subj_id = a['oc_id']
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
        for faculty in range(len(faculties)):
            news = parse_news(faculty)
            if not news:
                continue
            str_send = f'❗ *Опубліковано новину кафедри*\n' \
                       f'✔ [{mu.esc_md(news[0].title)}]({mu.esc_md(news[0].link)})'
            with DatabaseConnection() as db:
                conn, cursor = db
                cursor.execute(selectQuery, [faculties[faculty]])
                results = cursor.fetchall()
            for res in results:
                await mu.send_message(bot.send_message, chat_id=res[0], text=str_send, parse_mode='Markdown')
                await sleep(.05)
        await sleep(3600)  # 60 min


async def updater_posting():
    filename = temp_dir/'posting.txt'
    filename_num = temp_dir/'posting_start_num.txt'
    while True:
        if not path.isfile(filename):
            await sleep(10)
            continue
        with open(filename, 'r') as f:
            text = f.read()
        start_num = 0
        if path.isfile(filename_num):
            with open(filename_num, 'r') as f:
                start_num = int(f.read())
        selectQuery = "SELECT user_id FROM users"
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(selectQuery)
            users = cursor.fetchall()
        i = 0
        j = 0
        len_users = len(users)
        progress_message = (await bot.send_message(BOT_ADMIN, f'{start_num}/{len_users}')).message_id
        for n, user in enumerate(users, 1):
            if n <= start_num:
                continue
            if await mu.send_message(bot.send_message, chat_id=user[0], text=text, parse_mode='Markdown'):
                i += 1
            else:
                j += 1
            await bot.edit_message_text(f'{n}/{len_users}', BOT_ADMIN, progress_message)
            with open(filename_num, 'w') as f:
                f.write(str(n))
            await sleep(.1)
            if n % 100 == 0:
                await sleep(3)
        await bot.send_message(BOT_ADMIN, f"Отправлено: {i}\nНе отправлено: {j}")
        remove(filename)
        remove(filename_num)


__all__ = (updater_news, updater_record_book, update_users_record_book, updater_posting)
