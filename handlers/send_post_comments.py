from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, or_f

from utils.error_handling import error_handler
from utils.send_admins import send_message_manager
from database import requests as rq
from database.models import User
from config_data.config import Config, load_config
from filters.filter import validate_text_latin
from keyboards.send_post_keyboard import keyboard_continue, keyboard_ebu, keyboard_photo, keyboard_method

import logging
import asyncio
import random

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class PostComment(StatesGroup):
    model_state = State()
    year_state = State()
    script_state = State()
    sn_state = State()
    method_state = State()
    note_state = State()
    photo_state = State()


async def collecting_content(state: FSMContext, user_tg_id: int) -> (list, str):
    data = await state.get_data()
    model = data.get('model', '')
    year = data.get('year', '')
    if model:
        if year:
            year = f'{year} год'
            model = f'<b><u>Модель авто:</u></b> {model} {year}\n'
        else:
            model = f'<b><u>Модель авто:</u></b> {model}\n'
    ebu = data.get('ebu', '')
    if ebu:
        ebu = f'<b><u>Тип, номер ЭБУ:</u></b> {ebu}\n'
    script = data.get('script', '')
    if script:
        script = f'<b><u>Скрипт:</u></b> {script}\n'
    sn = data.get('sn', '')
    if sn:
        sn = f'<b><u>Серийный номер:</u></b> {sn}\n'
    method = data.get('method', '')
    if method:
        method = f'<b><u>Способ:</u></b> {method}\n'
    note = data.get('note', '')
    if note:
        note = f'<b><u>Примечание:</u></b> {note}\n'
    content_list = data.get('content', [])
    caption = f'{model}{ebu}{script}{sn}{method}{note}\n' \
              f'Материалы опубликованы <a href="tg://user?id={user_tg_id}">пользователем</a>'
    media_group = []
    if content_list:
        i = 0
        for photo in content_list:
            i += 1
            if i == 1:
                media_group.append(InputMediaPhoto(media=photo, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=photo))
    return media_group, caption


@router.message(F.text == 'Комментарии по софту и обзоры скриптов')
@error_handler
async def process_advertisement(message: Message, bot: Bot, state: FSMContext):
    logging.info('process_advertisement')
    await state.set_state(state=None)
    await state.clear()
    msg = await message.answer(text=f'Пришлите модель авто, обязательное условие пишите на <b>латинице</b> '
                                    f'(например: Ford Fusion)')
    logging.info(f'{msg.message_id}')
    await state.set_state(PostComment.model_state)


@router.message(F.text, StateFilter(PostComment.model_state))
@error_handler
async def get_model(message: Message, bot: Bot, state: FSMContext):
    logging.info('get_model')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки', 'Удалить публикацию']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    else:
        if validate_text_latin(text=message.text):
            await state.update_data(model=message.text)
            msg = await message.answer(text=f'Год производства авто (необязательно)',
                                       reply_markup=keyboard_continue())
            logging.info(f'{msg.message_id, message.message_id}')
            await state.set_state(PostComment.year_state)
        else:
            msg = await message.answer(text=f'Модель авто, должна обязательно написана на <b>латинице</b> '
                                            f'(например: Ford Fusion). Повторите ввод')
            logging.info(f'{msg.message_id, message.message_id}')


@router.message(F.text, StateFilter(PostComment.year_state))
@error_handler
async def get_year(message: Message, bot: Bot, state: FSMContext):
    logging.info('get_year')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки', 'Удалить публикацию']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    else:
        if message.text.isdigit() and 1950 < int(message.text) < 2030:
            await state.update_data(year=message.text)
            await message.delete()
            msg = await bot.edit_message_text(chat_id=message.from_user.id,
                                              text=f'Выберите тип ЭБУ;',
                                              message_id=message.message_id-1,
                                              reply_markup=keyboard_ebu())
            logging.info(f'{msg.message_id}')
        else:
            await message.delete()
            for i in range(5):
                try:
                    await bot.delete_message(chat_id=message.from_user.id,
                                             message_id=message.message_id - i)
                except:
                    pass
            msg = await message.answer(text=f'Год производства авто (необязательно) указан не корректно',
                                       reply_markup=keyboard_continue())
            logging.info(f'{msg.message_id, message.message_id}')


@router.callback_query(F.data.startswith('ebu_'))
@error_handler
async def get_type_ebu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'get_type_ebu {callback.message.chat.id}')
    ebu = callback.data.split('_')[-1]
    await state.update_data(ebu=ebu)
    msg = await callback.message.edit_text(text='Пришлите наименование скрипта (необязательно). '
                                                'Например:DASHBOARD/CAN_OBD/FORD/FORD OBD2/Fiesta 2006+(Mc9s12h256).',
                                           reply_markup=keyboard_continue())
    logging.info(f'{msg.message_id, callback.message.message_id}')
    await state.set_state(PostComment.script_state)


@router.message(F.text, StateFilter(PostComment.script_state))
@error_handler
async def request_sn(message: Message, bot: Bot, state: FSMContext):
    logging.info('request_sn')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки', 'Удалить публикацию']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    else:
        await state.update_data(script=message.text)
        await message.delete()
        logging.info(f'{message.message_id}')
        for i in range(5):
            try:
                await bot.delete_message(chat_id=message.from_user.id,
                                         message_id=message.message_id-i)
            except:
                pass
        msg = await message.answer(text='Пришлите серийный номер (необязательно)',
                                   reply_markup=keyboard_continue())
        logging.info(f'{msg.message_id, message.message_id}')
        await state.set_state(PostComment.sn_state)


@router.message(F.text, StateFilter(PostComment.sn_state))
@error_handler
async def get_sn(message: Message, bot: Bot, state: FSMContext):
    logging.info('get_sn')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки', 'Удалить публикацию']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    else:
        await message.delete()
        logging.info(f'{message.message_id}')
        for i in range(5):
            try:
                await bot.delete_message(chat_id=message.from_user.id,
                                         message_id=message.message_id - i)
            except:
                pass
        await state.update_data(sn=message.text)
        msg = await message.answer(text='Пришлите способ (необязательно)',
                                   reply_markup=keyboard_method())
        logging.info(f'{msg.message_id, message.message_id}')
        await state.set_state(PostComment.method_state)


@router.callback_query(F.data.startswith('method_'))
@error_handler
async def get_method(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info('get_method')
    method = callback.data.split('_')[-1]
    await state.update_data(method=method)
    await callback.message.edit_text(text='Пришлите примечание (необязательно). '
                                          'Кратко опишите процесс работы, если есть прикрепите фото, схемы,'
                                          ' подключение.',
                                     reply_markup=keyboard_continue())
    await state.set_state(PostComment.note_state)
    await callback.answer()


@router.message(F.text, StateFilter(PostComment.note_state))
@error_handler
async def get_note(message: Message, bot: Bot, state: FSMContext):
    logging.info('get_note')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки', 'Удалить публикацию']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    else:
        await state.update_data(note=message.text)
        await message.delete()
        media_group, caption = await collecting_content(state=state, user_tg_id=message.from_user.id)
        if media_group:
            await message.answer_media_group(media=media_group)
        else:
            await message.answer(text=caption)
        await message.answer(text='Материалы для публикации поста получены, можете добавить фотографию',
                             reply_markup=keyboard_photo())


@router.message(StateFilter(PostComment.photo_state), F.photo)
@error_handler
async def request_content_photo(message: Message, state: FSMContext, bot: Bot):
    logging.info(f'request_content_photo')
    await asyncio.sleep(random.random())
    data = await state.get_data()
    list_content = data.get('content', [])
    count = data.get('count', [])
    content = f'{message.photo[-1].file_id}'
    list_content.append(content)
    count.append(content)
    await state.update_data(content=list_content)
    await state.update_data(count=count)
    media_group, caption = await collecting_content(state=state, user_tg_id=message.from_user.id)
    if media_group:
        await message.answer_media_group(media=media_group)
    else:
        await message.answer(text=caption)
    if len(count) == 1:
        await message.answer(text='Добавьте еще фотографии или нажмите "Продолжить"',
                             reply_markup=keyboard_photo())


@router.callback_query(F.data == 'add_photo_post')
@error_handler
async def get_photo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'add_photo {callback.message.chat.id}')
    await callback.message.edit_text(text='Пришлите фотоматериалы 📸.',
                                     reply_markup=None)
    await state.update_data(count=[])
    await state.set_state(PostComment.photo_state)


@router.callback_query(F.data == 'pass_add_content')
@error_handler
async def pass_add_content(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'pass_add_content {callback.message.chat.id}')
    state_ = await state.get_state()
    if state_ == PostComment.year_state:
        await state.update_data(year='')
        await callback.message.edit_text(text=f'Выберите тип ЭБУ;',
                                         reply_markup=keyboard_ebu())
    elif state_ == PostComment.script_state:
        await state.update_data(script='')
        await state.set_state(PostComment.sn_state)
        await callback.message.edit_text(text='Пришлите серийный номер (необязательно)',
                                         reply_markup=keyboard_continue())
    elif state_ == PostComment.sn_state:
        await state.update_data(sn_state='')
        await callback.message.edit_text(text='Пришлите способ (необязательно)',
                                         reply_markup=keyboard_method())
        await state.set_state(PostComment.method_state)
    elif state_ == PostComment.method_state:
        await state.update_data(method_state='')
        await callback.message.edit_text(text='Пришлите примечание (необязательно). '
                                              'Кратко опишите процесс работы, если есть прикрепите фото, схемы,'
                                              ' подключение.',
                                         reply_markup=keyboard_continue())
        await state.set_state(PostComment.note_state)
    elif state_ == PostComment.note_state:
        await state.update_data(note_state='')
        await callback.message.delete()
        media_group, caption = await collecting_content(state=state, user_tg_id=callback.from_user.id)
        if media_group:
            await callback.message.answer_media_group(media=media_group)
        else:
            await callback.message.answer(text=caption)
        await callback.message.answer(text='Материалы для публикации поста получены, можете добавить фотографию',
                                      reply_markup=keyboard_photo())


@router.callback_query(F.data == 'post_publish')
@error_handler
async def get_photo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'get_photo {callback.message.chat.id}')
    await state.set_state(state=None)
    # data = await state.get_data()
    # model = data.get('model', '')
    # year = data.get('year', '')
    # if model:
    #     if year:
    #         year = f'{year} год'
    #         model = f'<b><u>Модель авто:</u></b> {model} {year}\n'
    #     else:
    #         model = f'<b><u>Модель авто:</u></b> {model}\n'
    # ebu = data.get('ebu', '')
    # script = data.get('script', '')
    # if script:
    #     script = f'<b><u>Скрипт:</u></b> {script}\n'
    # sn = data.get('sn', '')
    # if sn:
    #     sn = f'<b><u>Серийный номер:</u></b> {sn}\n'
    # method = data.get('method', '')
    # if method:
    #     method = f'<b><u>Способ:</u></b> {method}\n'
    # note = data.get('note', '')
    # if note:
    #     note = f'<b><u>Примечание:</u></b> {note}\n'
    # content_list = data.get('content', [])
    # caption = f'{model}{ebu}{script}{sn}{method}{note}'
    # if content_list:
    #     media_group = []
    #     i = 0
    #     for photo in content_list:
    #         i += 1
    #         if i == 1:
    #             media_group.append(InputMediaPhoto(media=photo, caption=caption))
    #         else:
    #             media_group.append(InputMediaPhoto(media=photo))
    media_group, caption = await collecting_content(state=state, user_tg_id=callback.from_user.id)
    group_peer_id = config.tg_bot.general_group
    message_thread_id = config.tg_bot.comment_topic
    if media_group:
        message_post = await bot.send_media_group(chat_id=group_peer_id,
                                                  media=media_group,
                                                  message_thread_id=message_thread_id)
        await rq.update_message_id(tg_id=callback.from_user.id,
                                   message_id=message_post[0].message_id,
                                   message_thread_id=message_thread_id)
    else:
        message_post = await bot.send_message(chat_id=group_peer_id,
                                              text=caption,
                                              message_thread_id=message_thread_id)
        await rq.update_message_id(tg_id=callback.from_user.id,
                                   message_id=message_post.message_id,
                                   message_thread_id=message_thread_id)
    await callback.message.edit_text(text=f'Ваши материалы опубликованы')
