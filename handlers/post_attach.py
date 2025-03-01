
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
    url_button = State()
    link_resource = State()


@router.message(F.text == '/post_attach')
@error_handler
async def post_attach(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_attach')
    await message.answer(text='Пришлите текст для поста, например: <code>Разместите материал с помощью бота</code>')
    await state.set_state(Attach.post_text)


@router.message(F.text, StateFilter(Attach.post_text))
@error_handler
async def post_text(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_text')
    await message.answer(text='Пришлите текст для кнопки, например: <code>РАЗМЕСТИТЬ</code>')
    await state.set_state(Attach.post_button)
    await state.update_data(post_text=message.text)


@router.message(F.text, StateFilter(Attach.post_button))
@error_handler
async def post_button(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_button')
    await message.answer(text=f'Пришлите ссылку для кнопки, например:'
                              f' <code>https://t.me/MyderatorGroupsBot?start</code>')
    await state.set_state(Attach.url_button)
    await state.update_data(text_button=message.text)


@router.message(F.text, StateFilter(Attach.url_button))
@error_handler
async def post_url(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('post_url')
    await message.answer(text='Пришлите ссылку на ресурс для размещения поста,'
                              ' бот обязательно должен быть в нем админом, например:'
                              ' <code>https://t.me/c/1327075982/84907</code>')
    await state.set_state(Attach.link_resource)
    await state.update_data(url_button=message.text)


@router.message(F.text, StateFilter(Attach.link_resource))
@error_handler
async def link_resource(message: Message, bot: Bot, state: FSMContext) -> None:
    logging.info('link_resource')
    await message.answer(text='Пост размещен в топиках группы')
    await state.set_state(state=None)
    data = await state.get_data()
    post_text = data['post_text']
    text_button = data['text_button']
    url_button = data['url_button']
    link_resource = message.text  # https://t.me/1327075982/143638
    chat_id = link_resource.split('/')[-2]
    message_thread_id = int(link_resource.split('/')[-1])
    button_1 = InlineKeyboardButton(text=text_button,
                                    url=url_button)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    msg = await bot.send_message(chat_id=config.tg_bot.general_group,
                                 text=post_text,
                                 reply_markup=keyboard,
                                 message_thread_id=message_thread_id)
    await bot.pin_chat_message(chat_id=config.tg_bot.general_group,
                               message_id=msg.message_id)
