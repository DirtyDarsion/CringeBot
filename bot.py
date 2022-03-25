import logging
import os
from random import choice

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.executor import start_webhook

from db import register_user, get_users
from func import is_not_private

from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


@dp.message_handler(lambda message: message.text.lower() == '+')
async def test_def(message: types.Message):
    register_user(message)

    message_text = 'Список кринж команд:\n\n' \
                   'кринж стат\n' \
                   'кринж кто'
    await message.answer(message_text)


@dp.message_handler(lambda message: message.text.lower() == 'кринж команды' and is_not_private(message))
async def test_def(message: types.Message):
    register_user(message)

    message_text = 'Список кринж команд:\n\n' \
                   'кринж стат\n' \
                   'кринж кто'
    await message.answer(message_text)


@dp.message_handler(lambda message: message.text.lower() == 'кринж стат' and is_not_private(message))
async def test_def(message: types.Message):
    register_user(message)

    users = get_users(message.chat.id)
    message_text = 'Список кринж команды:'
    for user in users:
        message_text += '\n' + user[0] + ', он же ' + user[1]

    await message.answer(message_text)


@dp.message_handler(lambda message: message.text.lower().startswith('кринж кто') and is_not_private(message))
async def test_def(message: types.Message):
    register_user(message)

    if len(message.text.split()) > 2:
        title = message.text.split()[2]
    else:
        await message.answer('Напиши третье слово')
        return

    users = get_users(message.chat.id)
    user = choice(users)
    message_text = f'На данный момент {title} это {user[0]}'

    await message.answer(message_text)


@dp.message_handler(lambda message: message.text.lower() == 'кринж погоняло')
async def test_def(message: types.Message):
    register_user(message)

    message_text = 'Самое время дать погоняло какому нибудь гомику, перешли любое его сообщение'
    await message.answer(message_text)


@dp.message_handler(lambda message: message.text.lower() == '.' and is_not_private(message))
async def test_def(message: types.Message):
    register_user(message)

    with open('trash.txt', 'a', encoding='UTF-8') as text:
        text.write('\n' + str(message))

    await message.reply('ok')


@dp.message_handler(lambda message: 'серgay' in message.text.lower() and is_not_private(message))
async def fuck_def(message: types.Message):
    register_user(message)
    await message.reply('Пошел нахуй!')


@dp.message_handler()
async def register_ower_messages(message: types.Message):
    register_user(message)


LOCAL = int(os.getenv('LOCAL_REPO'))

if LOCAL:
    if __name__ == '__main__':
        executor.start_polling(dp, skip_updates=True)
else:
    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO)
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
