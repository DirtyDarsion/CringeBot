import logging
from os import getenv
from random import choice, randint

from aiohttp import web

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, ChatTypeFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.storage.redis import DefaultKeyBuilder, RedisStorage
from aiogram.dispatcher.webhook.aiohttp_server import (
    SimpleRequestHandler,
    TokenBasedRequestHandler,
    setup_application,
)
from aiogram.utils.callback_data import CallbackData

from db import register_user, get_users, change_fuckname
from func import insults

from dotenv import load_dotenv
load_dotenv()


router = Router()


TOKEN = getenv('BOT_TOKEN')
LOCAL = int(getenv('LOCAL_REPO'))

HEROKU_APP_NAME = getenv('HEROKU_APP_NAME')
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = getenv('PORT', default=8000)
REDIS_DSN = "redis://127.0.0.1:6479"

# Global wars
user_data = {}

# Callback Factory
callback_fuckname = CallbackData('prefix', 'user_id')


# Class by fuckname
class Fuckname(StatesGroup):
    name = State()


@dp.message_handler(Text(startswith='кринж команды', ignore_case=True))
async def commands(message: types.Message):
    register_user(message)

    message_text = 'Список кринж команд:\n\n' \
                   '- статы\n' \
                   '- кто\n' \
                   '- погоняло\n' \
                   '- голосование'
    await message.answer(message_text)


@dp.message_handler(Text(startswith='статы', ignore_case=True))
async def stats(message: types.Message):
    register_user(message)

    users = get_users(message.chat.id)
    message_text = 'Список бойцов:\n'
    for user in users:
        message_text += '\n- ' + user['name'] + ', он же ' + user['username']

    await message.answer(message_text)


@dp.message_handler(Text(startswith='кто', ignore_case=True))
async def who(message: types.Message):
    register_user(message)

    if len(message.text.split()) > 1:
        title = ' '.join(message.text.split()[1:])
    else:
        await message.answer('Напиши второе слово')
        return

    users = get_users(message.chat.id)
    user = choice(users)
    message_text = f'На данный момент {title} это {user["name"]}'

    await message.answer(message_text)


@dp.message_handler(Text(startswith='погоняло', ignore_case=True))
async def fuckname_change(message: types.Message):
    register_user(message)

    buttons = []
    for user in get_users(message.chat.id):
        buttons.append(types.InlineKeyboardButton(
            text=user['name'],
            callback_data=callback_fuckname.new(user_id=user['user_id'])
        ))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    await message.answer('Выбирай жертву:', reply_markup=keyboard)


@dp.callback_query_handler(callback_fuckname.filter())
async def setname_start(call: types.CallbackQuery, callback_data: dict):
    await call.answer()

    user_data[call.from_user.id] = callback_data['user_id']
    await call.message.edit_text('Пиши новое погоняло:')
    await Fuckname.name.set()


@dp.message_handler(state=Fuckname.name)
async def setname_end(message: types.Message, state: FSMContext):
    await state.update_data(fuckname=message.text)
    data = await state.get_data()
    fuckname = data['fuckname']
    await state.finish()

    change_fuckname(message, user_data[message.from_user.id], fuckname)
    await message.answer('Готово!')


@dp.message_handler(Text('голосование', ignore_case=True))
async def start_poll(message: types.Message):
    register_user(message)

    await message.answer('Не работает')


@dp.message_handler(Text('.'))
async def test_def(message: types.Message):
    register_user(message)

    with open('trash.txt', 'a', encoding='UTF-8') as text:
        text.write('\n' + str(message))


@dp.message_handler(ChatTypeFilter(types.ChatType.GROUP))
async def register_ower_messages(message: types.Message):
    register_user(message)

    if randint(1, 25) == 1:
        await message.reply(random.choice(insults))


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    logging.warning('Shutting down..')

    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


def main():
    session = AiohttpSession()
    bot_settings = {"session": session, "parse_mode": "HTML"}
    bot = Bot(token=TOKEN, **bot_settings)
    storage = RedisStorage.from_url(REDIS_DSN, key_builder=DefaultKeyBuilder(with_bot_id=True))

    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)
    dispatcher.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dispatcher, bot=bot).register(app, path=WEBHOOK_PATH)
    TokenBasedRequestHandler(
        dispatcher=multibot_dispatcher,
        bot_settings=bot_settings,
    ).register(app, path=OTHER_BOTS_PATH)

    setup_application(app, main_dispatcher, bot=bot)
    setup_application(app, multibot_dispatcher)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

    logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    main()
