import asyncio
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.state import StatesGroup, State
from database import requests as rq
from keyboards import manager_keyboard as kb
import logging
from datetime import datetime
from utils.error_handling import error_handler

from database.models import Order
from config_data.config import Config, load_config

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class Manager(StatesGroup):
    reason = State()


@router.message(F.text == 'Удалить публикацию')
@error_handler
async def process_manager(message: Message, bot: Bot) -> None:
    logging.info('process_manager')
    list_order_publish = await rq.select_order_status_create_tg_id(status=rq.OrderStatus.publish,
                                                                   create_tg_id=message.from_user.id)
    if list_order_publish:
        order = list_order_publish[0]
        caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
        media_group = []
        i = 0
        for photo in order.photo.split(','):
            i += 1
            if i == 1:
                media_group.append(InputMediaPhoto(media=photo, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=photo))
        await message.answer_media_group(media=media_group)
        await message.answer(
            text=f'Объявление опубликовано в разделе <i>{order.type_order}</i> {order.time_publish}.\n'
                 f'Вы можете удалить пост если с момента публикации прошло менее 48 часов',
            reply_markup=kb.keyboard_delete(id_order=order.id))
    else:
        await message.answer(text='Опубликованных постов нет')


@router.callback_query(F.data.startswith('delete_'))
@error_handler
async def delete_order(callback: CallbackQuery, bot: Bot):
    logging.info(f'delete_order {callback.message.chat.id}')
    answer = callback.data.split('_')[-1]
    order: Order = await rq.select_order_id(order_id=int(answer))
    date_format = '%d-%m-%Y %H:%M'
    current_date = datetime.now().strftime('%d-%m-%Y %H:%M')
    delta_time = (datetime.strptime(current_date, date_format) - datetime.strptime(order.time_publish, date_format))
    if delta_time.days < 2:
        message_chat = order.chat_message
        try:
            await bot.delete_message(chat_id=message_chat.split('!')[1].split('/')[0],
                                     message_id=message_chat.split('!')[0])
            await callback.message.edit_text(text='Пост успешно удален',
                                             reply_markup=None)
        except:
            await callback.message.edit_text(text='Пост для удаления в группе не найден,'
                                                  ' возможно вы удалили его самостоятельно',
                                             reply_markup=None)
        await rq.update_order_status(order_id=order.id, status=rq.OrderStatus.delete)

    else:
        await callback.message.edit_text(text='Пост не может быть удален так как прошло более 48 часов',
                                         reply_markup=None)
        await rq.update_order_status(order_id=order.id, status=rq.OrderStatus.old)
        await asyncio.sleep(1)
    await recursion_publish_delete(callback=callback)
    await callback.answer()


async def recursion_publish_delete(callback: CallbackQuery):
    logging.info('recursion_publish_delete')
    list_order_publish = await rq.select_order_status_create_tg_id(status=rq.OrderStatus.publish,
                                                                   create_tg_id=callback.from_user.id)
    if list_order_publish:
        order = list_order_publish[0]
        caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
        media_group = []
        i = 0
        for photo in order.photo.split(','):
            i += 1
            if i == 1:
                media_group.append(InputMediaPhoto(media=photo, caption=caption))
            else:
                media_group.append(InputMediaPhoto(media=photo))
        await callback.message.answer_media_group(media=media_group)
        await callback.message.answer(
            text=f'Объявление опубликовано в разделе <i>{order.type_order}</i> {order.time_publish}.\n'
                 f'Вы можете удалить пост если с момента публикации прошло менее 48 часов',
            reply_markup=kb.keyboard_delete(id_order=order.id))
    else:
        await callback.answer(text='Опубликованных постов нет', show_alert=True)
