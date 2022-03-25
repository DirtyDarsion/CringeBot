import os

import psycopg2

from dotenv import load_dotenv
load_dotenv()


DBNAME = os.getenv('DB_NAME')
USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')


def connect():
    conn = psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST)
    conn.autocommit = True
    cursor = conn.cursor()
    return conn, cursor


def check_user_in_chat(chat_id, tg_id):
    conn, cursor = connect()
    cursor.execute(f'SELECT tg_id FROM users WHERE chat_id = {chat_id} AND tg_id = {tg_id}')
    already = False
    for row in cursor:
        if row:
            already = True
    conn.close()
    return already


def register_user(message):
    chat_id = message.chat.id
    tg_id = message.from_user.id
    tg_username = message.from_user.username
    tg_firstname = message.from_user.first_name

    user_registered = check_user_in_chat(chat_id, tg_id)

    if not user_registered:
        conn, cursor = connect()
        cursor.execute(f'''INSERT INTO users VALUES ({chat_id}, {tg_id}, '{tg_username}', '{tg_firstname}')''')
        conn.close()


def get_users(chat_id):
    conn, cursor = connect()
    cursor.execute(f'SELECT tg_firstname, fuckname, tg_username, tg_id FROM users WHERE chat_id = {chat_id}')

    users = []
    for row in cursor:
        if row[1]:
            name = row[1]
        else:
            name = row[0]
        users.append({
            'name': name,
            'username': row[2],
            'user_id': row[3],
        })
    conn.close()

    return users


def change_fuckname(message, tg_id, fuckname):
    conn, cursor = connect()
    chat_id = message.chat.id
    cursor.execute(f'''UPDATE users SET fuckname = '{fuckname}' WHERE chat_id = {chat_id} AND tg_id = {tg_id}''')
    conn.close()
