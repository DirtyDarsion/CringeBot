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
    cursor.execute(f'''SELECT tg_firstname, fuckname, tg_username, tg_id, is_king, total_owner_king
                       FROM users WHERE chat_id = {chat_id} ORDER By is_king DESC''')

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
            'is_king': row[4],
            'total_owner_king': row[5],
        })
    conn.close()

    return users


def get_users_poll(chat_id):
    conn, cursor = connect()
    cursor.execute(f'''SELECT tg_firstname, fuckname, tg_id, vote_count
                       FROM users WHERE chat_id = {chat_id} ORDER BY vote_count DESC, total_owner_king DESC''')

    users = []
    for row in cursor:
        if row[1]:
            name = row[1]
        else:
            name = row[0]
        users.append({
            'name': name,
            'user_id': row[2],
            'vote_count': row[3],
        })
    conn.close()

    return users


def add_vote(chat_id, tg_id):
    conn, cursor = connect()
    cursor.execute(f'UPDATE users SET vote_count = vote_count + 1 WHERE chat_id = {chat_id} AND tg_id = {tg_id}')
    conn.close()


def get_poll_data(chat_id):
    conn, cursor = connect()
    cursor.execute(f'SELECT user_id FROM poll_data WHERE chat_id = {chat_id}')

    users = []
    for row in cursor:
        users.append(row[0])
    conn.close()

    return users


def add_user_to_poll_data(chat_id, user_id):
    conn, cursor = connect()
    cursor.execute(f'INSERT INTO poll_data (user_id, chat_id) VALUES ({user_id}, {chat_id})')
    conn.close()


def clear_poll_data(chat_id):
    conn, cursor = connect()
    cursor.execute(f'DELETE FROM poll_data WHERE chat_id = {chat_id}')
    conn.close()


def set_new_king(chat_id, user):
    conn, cursor = connect()
    cursor.execute(f'UPDATE users SET vote_count = 0, is_king = FALSE WHERE chat_id = {chat_id}')
    cursor.execute(f'''UPDATE users SET is_king = TRUE, total_owner_king = total_owner_king + 1 
                       WHERE chat_id = {chat_id} AND tg_id = {user["user_id"]}''')
    conn.close()


def change_fuckname(message, tg_id, fuckname):
    conn, cursor = connect()
    chat_id = message.chat.id
    cursor.execute(f'''UPDATE users SET fuckname = '{fuckname}' WHERE chat_id = {chat_id} AND tg_id = {tg_id}''')
    conn.close()


def clear_vote_count():
    conn, cursor = connect()
    cursor.execute(f'''UPDATE users SET vote_count = 0''')
    conn.close()
