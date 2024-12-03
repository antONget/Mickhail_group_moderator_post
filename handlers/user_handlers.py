import asyncio
import random
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, StateFilter
from filters.admin_filter import check_manager, check_super_admin
from database import requests as rq
from keyboards import user_keyboard as kb
import logging
from typing import List
from utils.error_handling import error_handler
from utils.send_admins import send_message_manager
from aiogram.utils.media_group import MediaGroupBuilder
router = Router()
router.message.filter(F.chat.type == "private")


# Определение состояний
class User(StatesGroup):
    description = State()
    photo = State()
    info = State()


@router.message(CommandStart())
@error_handler
async def process_press_start(message: Message, bot: Bot) -> None:
    logging.info('process_press_start')
    if message.from_user.username:
        username = message.from_user.username
    else:
        username = 'USER'
    data_user = {'tg_id': message.from_user.id, 'username': username}
    await rq.add_user(data=data_user)
    if await check_manager(telegram_id=message.from_user.id) or await check_super_admin(telegram_id=message.from_user.id):
        await message.answer(text='Добро пожаловать! Этот бот для постинга ваших рекламных сообщений в группу.'
                                  ' Для публикации рекламы выберите раздел',
                             reply_markup=kb.keyboard_main_manager())
    else:
        await message.answer(text='Добро пожаловать! Этот бот для постинга ваших рекламных сообщений в группу.'
                                  ' Для публикации рекламы выберите раздел',
                             reply_markup=kb.keyboard_main_button())


@router.message(lambda message: message.text in ['Частное объявление', 'Коммерческое объявление'])
@error_handler
async def process_advertisement(message: Message, bot: Bot, state: FSMContext):
    logging.info('process_advertisement')
    await state.update_data(type_order=message.text)
    await message.answer(text='<b>Пожалуйста ознакомьтесь с правилами размещения объявления.</b>\n'
                              'Разрешается к продаже только свое оборудование новое или бу, но только в'
                              ' единичных экземплярах. При продаже выставлять только свои фото.'
                              ' Ссылки на интернет ресурсы не приветствуются и будут удаляться.\n'
                              'Цены устанавливает сам продавец и ему решать по какой цене он продаст свой товар.\n'
                              'Торг приветствуется. При обоюдном решении переходим в лс для дальнейшего решения.\n'
                              'После продажи и получении товара обязательно отписываемся о сделке (для чистки чата).')
    await asyncio.sleep(5)
    await message.answer(text='Для размещение вашего объявления в выбранной категории пришлите боту по его запросу'
                              ' последовательно:\n'
                              '1.📝 <u>Описание объявления</u>\n'
                              '2.📸 <u>Фотоматериал</u>\n'
                              '3.☎️ <u>Контактная информация</u>\n')
    await message.answer(text='Пришлите описание вашего объявления 📝.')
    await state.set_state(User.description)


@router.message(F.text, StateFilter(User.description))
@error_handler
async def get_description(message: Message, bot: Bot, state: FSMContext):
    logging.info('get_description')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    await state.update_data(description=message.text)
    await message.answer(text='Пришлите фотоматериалы 📸.')
    await state.set_state(User.photo)
    await state.update_data(content=[])
    await state.update_data(count=[])


@router.message(StateFilter(User.photo), F.photo)
@error_handler
async def request_content_photo(message: Message, state: FSMContext, bot: Bot):
    logging.info(f'request_content_photo {message.photo[-1].file_id}')
    await asyncio.sleep(random.random())
    data = await state.get_data()
    list_content = data.get('content', [])
    count = data.get('count', [])
    content = message.photo[-1].file_id
    list_content.append(content)
    count.append(content)
    await state.update_data(content=list_content)
    await state.update_data(count=count)
    if len(count) == 1:
        await message.answer(text='Добавьте еще фотографии или нажмите "Продолжить"',
                             reply_markup=kb.keyboard_continue())


@router.callback_query(F.data == 'add_photo')
@error_handler
async def get_photo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'add_photo {callback.message.chat.id}')
    await callback.message.edit_text(text='Пришлите фотоматериалы 📸.',
                                     reply_markup=None)
    await state.update_data(count=[])
    await state.set_state(User.photo)


@router.callback_query(F.data == 'continue')
@error_handler
async def get_photo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'get_photo {callback.message.chat.id}')
    await state.set_state(state=None)
    await callback.message.edit_text(text='Пришлите контактную информацию ☎️.',
                                     reply_markup=None)
    await state.set_state(User.info)


@router.message(F.text, StateFilter(User.info))
@error_handler
async def get_description(message: Message, bot: Bot, state: FSMContext):
    logging.info('get_description')
    if message.text in ['Частное объявление', 'Коммерческое объявление', 'Услуги', 'Заявки']:
        await state.set_state(state=None)
        await message.answer('Отправка была прервана...')
        return
    await state.update_data(info=message.text)
    await message.answer(text='Благодарим вас за предоставленные материалы, ваша объявление отправлено на модерацию,'
                              ' ожидайте публикации')
    data = await state.get_data()
    data_order = {'type_order': data['type_order'], 'create_tg_id': message.from_user.id,
                  'description': data['description'], 'photo': ','.join(data['content']),
                  'info': data['info'], 'status': rq.OrderStatus.create}
    await rq.add_order(data=data_order)
    await send_message_manager(bot=bot, text=f'Пользователь @{message.from_user.username} оставил заявку на размещение'
                                             f'в категории {data["type_order"]}')
    await state.set_state(state=None)

    # caption = data['description'] + "\n" + "\n" + data['info']
    # media_group = []
    #
    # # media_group.add_photo(media="https://picsum.photos/200/300")
    # # Dynamically add photo with known type without using separate method
    # i = 0
    # for photo in data['content']:
    #     i += 1
    #     if i == 1:
    #         media_group.append(InputMediaPhoto(media=photo, caption=caption))
    #     else:
    #         media_group.append(InputMediaPhoto(media=photo))

    # # ... or video
    # media_group.add(type="video", media=FSInputFile("media/video.mp4"))
    # await bot.send_media_group(chat_id=-1002291300776, media=media_group, message_thread_id=161)


@router.message(F.text == 'Услуги')
@error_handler
async def process_services(message: Message, bot: Bot, state: FSMContext):
    logging.info('process_services')
    await message.answer(text='Выберите категорию услуги для размещения',
                         reply_markup=kb.keyboard_services())


@router.callback_query(F.data == 'paid')
@router.callback_query(F.data == 'free_charge')
@error_handler
async def services_publish(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'services_publish {callback.message.chat.id}')
    await callback.message.delete()
    if callback.data == 'paid':
        type_order = 'Платная услуга'
    elif callback.data == 'free_charge':
        type_order = 'Бесплатная услуга'
    await state.update_data(type_order=type_order)
    await callback.message.answer(text='<b>Пожалуйста ознакомьтесь с правилами размещения услуги.</b>\n'
                                       'Разрешается к продаже только свое оборудование новое или бу, но только в'
                                       ' единичных экземплярах. При продаже выставлять только свои фото.'
                                       ' Ссылки на интернет ресурсы не приветствуются и будут удаляться.\n'
                                       'Цены устанавливает сам продавец и ему решать по какой цене он'
                                       ' продаст свой товар.\n'
                                       'Торг приветствуется. При обоюдном решении переходим в лс для'
                                       ' дальнейшего решения.\n'
                                       'После продажи и получении товара обязательно отписываемся о сделке'
                                       ' (для чистки чата).')
    await asyncio.sleep(5)
    await callback.message.answer(text='Для размещение вашего объявления в выбранной категории пришлите'
                                       ' боту по его запросу последовательно:\n'
                                       '1.📝 <u>Описание услуги</u>\n'
                                       '2.📸 <u>Фотоматериал</u>\n'
                                       '3.☎️ <u>Контактная информация</u>\n')
    await callback.message.answer(text='Пришлите описание вашей услуги 📝.')
    await state.set_state(User.description)