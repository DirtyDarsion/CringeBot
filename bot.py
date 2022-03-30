import logging
import os
import random
from random import choice, randint

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, ChatTypeFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.executor import start_webhook
from aiogram.utils.callback_data import CallbackData
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db import register_user, get_users, get_users_poll, change_fuckname, add_vote, new_king
from other import insults

from dotenv import load_dotenv
load_dotenv()


TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)

# Global wars
user_data = {}
poll_data = []

# Callback Factory
callback_fuckname = CallbackData('fuckname', 'user_id')
callback_poll = CallbackData('poll', 'user_id', 'users')


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
        if user['is_king']:
            king_text = ', <b>Действующий кринж король!</b>'
        else:
            king_text = ''
        message_text += '\n- ' + user['name'] + king_text

    await message.answer(message_text, parse_mode='HTML')


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


# Poll defs
def keyboard_and_text_poll(users):
    buttons = []
    for user in users:
        buttons.append(types.InlineKeyboardButton(
            text=user['name'],
            callback_data=callback_poll.new(user_id=user['user_id'], users='text')
        ))
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    message_text = 'Запсукаем голосование за титул нового кринж короля:'
    for user in users:
        message_text += f'\n- {user["name"]}, проголосовали: {user.get("vote_count", 0)}'
    return keyboard, message_text


async def update_poll_message(message: types.Message):
    users = get_users_poll(message.chat.id)
    keyboard, message_text = keyboard_and_text_poll(users)

    await message.answer(message_text, reply_markup=keyboard)


@dp.message_handler(Text('голосование', ignore_case=True))
async def start_poll(message: types.Message):
    register_user(message)

    users = get_users(message.chat.id)
    keyboard, message_text = keyboard_and_text_poll(users)

    await message.answer(message_text, reply_markup=keyboard)


@dp.callback_query_handler(callback_poll.filter())
async def poll_refresh(call: types.CallbackQuery, callback_data: dict):
    if call.from_user.id in poll_data:
        await call.answer('Ты уже проголосовал')
        return

    await call.answer()
    add_vote(call.message.chat.id, callback_data['user_id'])

    poll_data.append(call.from_user.id)
    count_chat_users = await bot.get_chat_member_count(call.message.chat.id)
    if len(poll_data) == count_chat_users - 1:
        user = get_users_poll(call.message.chat.id)[0]
        await call.message.edit_text(f'Поприветствуем нового кринж короля: <b>{user["name"]}</b>', parse_mode='HTML')
        new_king(call.message.chat.id, user)
        poll_data.clear()
    else:
        await update_poll_message(call.message)


@dp.message_handler(ChatTypeFilter(types.ChatType.GROUP))
async def register_ower_messages(message: types.Message):
    register_user(message)

    if randint(1, 20) == 1:
        await message.reply(random.choice(insults))


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    logging.warning('Shutting down..')

    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()

    logging.warning('Bye!')


LOCAL = int(os.getenv('LOCAL_REPO'))
if LOCAL:
    if __name__ == '__main__':
        executor.start_polling(dp, skip_updates=True)
else:
    if __name__ == '__main__':
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            skip_updates=True,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
