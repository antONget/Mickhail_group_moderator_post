
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database import requests as rq
import logging
from config_data.config import load_config, Config
from utils.error_handling import error_handler

router = Router()
config: Config = load_config()
router.message.filter(F.chat.type == "private")


# Определение состояний
class Attach(StatesGroup):
    post_text = State()
    post_button = State()


@router.message(F.text == '/post_attach')
@error_handler
async def post_attach(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_attach')
    await message.answer(text='Пришлите текст для поста ')
    await state.set_state(Attach.post_text)


@router.message(F.text, StateFilter(Attach.post_text))
@error_handler
async def post_text(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_text')
    await message.answer(text='Пришлите текст для кнопки')
    await state.set_state(Attach.post_button)
    await state.update_data(post_text=message.text)


@router.message(F.text, StateFilter(Attach.post_button))
@error_handler
async def post_button(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_button')
    await message.answer(text='Пост размещен в топиках группы')
    await state.set_state(state=None)
    await state.update_data(post_button=message.text)
    groups = await rq.get_groups()
    data = await state.get_data()
    button_1 = InlineKeyboardButton(text=message.text, url='https://t.me/MyderatorGroupsBot')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    for group in groups:
        await bot.send_message(chat_id=config.tg_bot.general_group,
                               text=data['post_text'],
                               reply_markup=keyboard,
                               message_thread_id=group.peer_id_test)
