import asyncio
import random
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, StateFilter
from filters.admin_filter import check_manager, check_super_admin
from database import requests as rq
from keyboards import manager_keyboard as kb
import logging
from datetime import datetime
from utils.error_handling import error_handler
from utils.send_admins import send_message_manager
from database.models import User, Order
from config_data.config import Config, load_config

config: Config = load_config()
router = Router()
router.message.filter(F.chat.type == "private")


class Manager(StatesGroup):
    reason = State()


@router.message(F.text == 'Заявки')
@error_handler
async def process_manager(message: Message, bot: Bot) -> None:
    logging.info('process_manager')
    # получаем количество заявок по категориям
    list_order_create = await rq.select_order_status(status=rq.OrderStatus.create)
    list_order_publish = await rq.select_order_status(status=rq.OrderStatus.publish)
    list_order_cancel = await rq.select_order_status(status=rq.OrderStatus.cancel)
    count_create = len(list_order_create)
    count_publish = len(list_order_publish)
    count_cancel = len(list_order_cancel)
    await message.answer(text='Выберите раздел',
                         reply_markup=kb.keyboard_process_order(count_create=count_create,
                                                                count_publish=count_publish,
                                                                count_cancel=count_cancel))


@router.callback_query(F.data.startswith('order_'))
@error_handler
async def manager_oreders(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'manager_oreders {callback.message.chat.id}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    answer = callback.data.split('_')[-1]
    # если выбраны созданные заявки
    if answer == 'create':
        try:
            # список созданных заявок
            list_order_create = await rq.select_order_status(status=rq.OrderStatus.create)
            # если созданные заявки есть
            if list_order_create:
                # получаем первую заявку из списка
                order = list_order_create[0]
                # формируем текст поста из описания и контактов
                caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
                # собираем фото в медиагруппу
                media_group = []
                i = 0
                for photo in order.photo.split(','):
                    i += 1
                    if i == 1:
                        type_content = photo.split('!')[-1]
                        if type_content == 'p':
                            media_group.append(InputMediaPhoto(media=photo.split('!')[0], caption=caption))
                        else:
                            media_group.append(InputMediaVideo(media=photo.split('!')[0], caption=caption))
                    else:
                        type_content = photo.split('!')[-1]
                        if type_content == 'p':
                            media_group.append(InputMediaPhoto(media=photo.split('!')[0]))
                        else:
                            media_group.append(InputMediaVideo(media=photo.split('!')[0]))
                # отправляем медиагруппу
                await callback.message.answer_media_group(media=media_group)
                # информация о создателе заявки
                user_order: User = await rq.get_user(tg_id=order.create_tg_id)
                print(order.create_tg_id)
                # отправляем информацию о заказчике
                await callback.message.answer(text=f'Получена заявка от <a href="tg://user?id={user_order.username}">{user_order.username}</a> для размещения в разделе: <i>{order.type_order}</i>.\n'
                                                   f'Вы можете отправить пост на публикацию или отменить публикацию заявки'
                                                   f'указав причину отказа',
                                              reply_markup=kb.keyboard_publish(id_order=order.id))
            # иначе информируем что заявок нет
            else:
                await callback.answer(text='Заявок на модерацию для публикации в группах нет', show_alert=True)
        except Exception as e:
            logging.info(f'{e}')
            list_order_create = await rq.select_order_status(status=rq.OrderStatus.create)
            await rq.update_order_status(order_id=list_order_create[0].id, status=rq.OrderStatus.error)
            await callback.message.answer(text=f'При выводе заявки №{list_order_create[0].id} возникла проблема')
            await bot.send_message(chat_id=config.tg_bot.support_id,
                                   text=f'При выводе заявки №{list_order_create[0].id} возникла проблема\n')
            await process_manager(message=callback.message, bot=bot)

    elif answer == 'publish':
        list_order_publish = await rq.select_order_status(status=rq.OrderStatus.publish)
        if list_order_publish:
            order = list_order_publish[0]
            caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
            media_group = []
            i = 0
            for photo in order.photo.split(','):
                i += 1
                if i == 1:
                    if '!' not in photo:
                        media_group.append(InputMediaPhoto(media=photo, caption=caption))
                    else:
                        type_content = photo.split('!')[-1]
                        if type_content == 'p':
                            media_group.append(InputMediaPhoto(media=photo.split('!')[0], caption=caption))
                        else:
                            media_group.append(InputMediaVideo(media=photo.split('!')[0], caption=caption))
                else:
                    if '!' not in photo:
                        media_group.append(InputMediaPhoto(media=photo))
                    else:
                        type_content = photo.split('!')[-1]
                        if type_content == 'p':
                            media_group.append(InputMediaPhoto(media=photo.split('!')[0]))
                        else:
                            media_group.append(InputMediaVideo(media=photo.split('!')[0]))
            await callback.message.answer_media_group(media=media_group)
            user_order: User = await rq.get_user(tg_id=order.create_tg_id)
            await callback.message.answer(text=f'Объявление от <a href="tg://user?id={user_order.username}">{user_order.username}</a>'
                                               f' опубликовано в разделе <i>{order.type_order}</i> {order.time_publish}.\n'
                                               f'Вы можете удалить пост если с момента публикации прошло менее 48 часов',
                                          reply_markup=kb.keyboard_delete(id_order=order.id))
            await state.update_data(count_publish=0)
        else:
            await callback.answer(text='Заявок на модерацию для публикации в группах нет', show_alert=True)
    elif answer == 'cancel':
        list_order_cancel = await rq.select_order_status(status=rq.OrderStatus.cancel)
        if list_order_cancel:
            order = list_order_cancel[0]
            caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
            media_group = []
            i = 0
            for photo in order.photo.split(','):
                i += 1
                if i == 1:
                    type_content = photo.split('!')[-1]
                    if type_content == 'p':
                        media_group.append(InputMediaPhoto(media=photo.split('!')[0], caption=caption))
                    else:
                        media_group.append(InputMediaVideo(media=photo.split('!')[0], caption=caption))
                else:
                    type_content = photo.split('!')[-1]
                    if type_content == 'p':
                        media_group.append(InputMediaPhoto(media=photo.split('!')[0]))
                    else:
                        media_group.append(InputMediaVideo(media=photo.split('!')[0]))
            await callback.message.answer_media_group(media=media_group)
            user_order: User = await rq.get_user(tg_id=order.create_tg_id)

        else:
            await callback.answer(text='Отмененные заявки отсутствуют', show_alert=True)
    await callback.answer()


@router.callback_query(F.data.startswith('publish_'))
@error_handler
async def publish_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'publish_order {callback.message.chat.id}')
    # получаем список заявок на размещение
    list_order_create = await rq.select_order_status(status=rq.OrderStatus.create)
    logging.info(list_order_create)
    # если есть заявки на размещение
    if list_order_create:
        # обновляем статус заявки
        await rq.update_order_status(order_id=list_order_create[0].id, status=rq.OrderStatus.publish)
        # получаем информацию о заявке
        order = await rq.select_order_id(order_id=list_order_create[0].id)
        # формируем текст поста
        caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
        # формируем медиагруппу
        media_group = []
        i = 0
        for photo in order.photo.split(','):
            i += 1
            if i == 1:
                type_content = photo.split('!')[-1]
                if type_content == 'p':
                    media_group.append(InputMediaPhoto(media=photo.split('!')[0], caption=caption))
                else:
                    media_group.append(InputMediaVideo(media=photo.split('!')[0], caption=caption))
            else:
                type_content = photo.split('!')[-1]
                if type_content == 'p':
                    media_group.append(InputMediaPhoto(media=photo.split('!')[0]))
                else:
                    media_group.append(InputMediaVideo(media=photo.split('!')[0]))
        group = await rq.get_group_topic(type_group=order.type_order)
        msg = await bot.send_media_group(chat_id=config.tg_bot.general_group,
                                         media=media_group,
                                         message_thread_id=group.peer_id)
        await rq.update_order_message(order_id=list_order_create[0].id,
                                      message=f'{msg[0].message_id}!{msg[0].chat.id}/{msg[0].message_thread_id}')
        await rq.update_order_datetime(order_id=list_order_create[0].id,
                                       date_teme=datetime.now().strftime('%d-%m-%Y %H:%M'))
        for j in range(i):
            await bot.delete_message(chat_id=callback.message.chat.id,
                                     message_id=callback.message.message_id - j - 1)
        await callback.message.edit_text(text='Заявка успешна опубликована', reply_markup=None)
        user_post: User = await rq.get_user(tg_id=order.create_tg_id)
        await send_message_manager(bot=bot,
                                   text=f'Объявление от <a href="tg://user?id={user_post.tg_id}">@{user_post.username}</a>'
                                        f' опубликовано в разделе <i>{order.type_order}</i>.\n')
        await bot.send_message(chat_id=order.create_tg_id,
                               text=f'Ваша заявка опубликована в разделе {order.type_order}')
        await recursion_publish(message=callback.message)
    # иначе информируем что заявок нет
    else:
        await callback.answer(text='Заявок на модерацию для публикации в группах нет', show_alert=True)


async def recursion_publish(message: Message):
    logging.info('recursiv_publish')
    list_order_create = await rq.select_order_status(status=rq.OrderStatus.create)
    if list_order_create:
        order = list_order_create[0]
        caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
        media_group = []
        i = 0
        for photo in order.photo.split(','):
            i += 1
            if i == 1:
                type_content = photo.split('!')[-1]
                if type_content == 'p':
                    media_group.append(InputMediaPhoto(media=photo.split('!')[0], caption=caption))
                else:
                    media_group.append(InputMediaVideo(media=photo.split('!')[0], caption=caption))
            else:
                type_content = photo.split('!')[-1]
                if type_content == 'p':
                    media_group.append(InputMediaPhoto(media=photo.split('!')[0]))
                else:
                    media_group.append(InputMediaVideo(media=photo.split('!')[0]))
        await message.answer_media_group(media=media_group)
        user_order: User = await rq.get_user(tg_id=order.create_tg_id)
        await message.answer(
            text=f'Получена заявка от <a href="tg://user?id={user_order.username}">{user_order.username}</a> для размещения в разделе: <i>{order.type_order}</i>.\n'
                 f'Вы можете отправить пост на публикацию или отменить публикацию заявки'
                 f'указав причину отказа',
            reply_markup=kb.keyboard_publish(id_order=order.id))
    else:
        await message.answer(text='Заявок на модерацию для публикации в группах нет')


@router.callback_query(F.data.startswith('cancel_'))
@error_handler
async def cancel_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'cancel_order {callback.message.chat.id}')
    answer = callback.data.split('_')[-1]
    await callback.message.edit_text(text=f'Укажите причину отмены публикации')
    order: Order = await rq.select_order_id(order_id=int(answer))
    await state.update_data(order_cancel=order)
    await state.set_state(Manager.reason)


@router.message(StateFilter(Manager.reason))
@error_handler
async def reason_cancel_order(message: Message, state: FSMContext, bot: Bot):
    logging.info(f'reason_cancel_order {message.chat.id}')
    data = await state.get_data()
    order = data['order_cancel']
    reason = message.text
    await bot.send_message(chat_id=order.create_tg_id,
                           text=f'Ваша заявка №{order.id} на размещение в разделе {order.type_order}'
                                f' отменена по причине {reason}')
    await rq.update_order_status(order_id=order.id, status=rq.OrderStatus.cancel)
    user_post: User = await rq.get_user(tg_id=order.create_tg_id)
    await send_message_manager(bot=bot,
                               text=f'Публикация объявления от '
                                    f'<a href="tg://user?id={user_post.tg_id}">@{user_post.username}</a> отмена.\n')
    await recursion_publish(message=message)
    await state.set_state(state=None)


@router.callback_query(F.data.startswith('delete_'))
@error_handler
async def delete_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
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
            count_content = len(order.photo.split(','))
            if count_content > 1:
                for i in range(count_content - 1):
                    message_id = int(message_chat.split('!')[0]) + 1 + i
                    await bot.delete_message(chat_id=message_chat.split('!')[1].split('/')[0],
                                             message_id=message_id)
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
    list_order_publish = await rq.select_order_status(status=rq.OrderStatus.publish)
    if list_order_publish:
        order = list_order_publish[0]
        caption = f'{order.description}\n\n{order.info}\n\nСтоимость: {order.cost} ₽'
        media_group = []
        i = 0
        for photo in order.photo.split(','):
            i += 1
            if i == 1:
                type_content = photo.split('!')[-1]
                if type_content == 'p':
                    media_group.append(InputMediaPhoto(media=photo.split('!')[0], caption=caption))
                else:
                    media_group.append(InputMediaVideo(media=photo.split('!')[0], caption=caption))
            else:
                type_content = photo.split('!')[-1]
                if type_content == 'p':
                    media_group.append(InputMediaPhoto(media=photo.split('!')[0]))
                else:
                    media_group.append(InputMediaVideo(media=photo.split('!')[0]))
        await callback.message.answer_media_group(media=media_group)
        user_order: User = await rq.get_user(tg_id=order.create_tg_id)
        await callback.message.answer(
            text=f'Объявление от <a href="tg://user?id={user_order.username}">{user_order.username}</a>'
                 f' опубликовано в разделе <i>{order.type_order}</i> {order.time_publish}.\n'
                 f'Вы можете удалить пост если с момента публикации прошло менее 48 часов',
            reply_markup=kb.keyboard_delete(id_order=order.id))
    else:
        await callback.answer(text='Заявок на модерацию для публикации в группах нет', show_alert=True)


@router.callback_query(F.data.startswith('pubcont_'))
@error_handler
async def delete_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'delete_order {callback.message.chat.id}')
    answer = callback.data.split('_')[-1]
