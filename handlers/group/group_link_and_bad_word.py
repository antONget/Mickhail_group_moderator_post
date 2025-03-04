import asyncio

from aiogram import Router, Bot
from aiogram.types import Message, MessageReactionUpdated

from filters.admin_chat import IsAdminChat
from filters.groups_chat import IsGroup
from config_data.config import banned_messages, words_of_gratitude
from database import requests as rq
from database.models import MessageId
from config_data.config import Config, load_config
from handlers.group.word_of_gratitude import word_of_gradit

import logging
import datetime

config: Config = load_config()
router = Router()


@router.message(IsGroup())
async def check_messages(message: Message, bot: Bot):
    """
    Обрабатываем любое действие в группе
    :param message:
    :param bot:
    :return:
    """
    logging.info(f'check_messages {message.message_thread_id} {message.chat.id} {message.from_user.id}')
    # если апдейт пришел из топика "Частные объявления. (Ларек Мастера)"
    if message.message_thread_id == 67830:
        # если отправлено сообщение как ответное
        if message.reply_to_message.text:
            pass
        # все соощение не от списка пользователей
        elif message.from_user.id not in [7727341378, 1492644981, 1572221921, 843554518]:
            await message.delete()
            msg = await message.answer(text='В этом разделе можно публиковать посты только через бота'
                                            ' @MyderatorGroupsBot.\n'
                                            'Оставьте вашу заявку в боте, мы ее рассмотрим и опубликуем!')
            await asyncio.sleep(10)
            await msg.delete()
            return
    # добавляем информацию об отправленном сообщении в БД -> MessageId
    print(message)
    await rq.update_message_id(tg_id=message.from_user.id,
                               message_id=message.message_id,
                               message_thread_id=message.message_thread_id)
    # получаем текст сообщения
    text = message.text
    text_ = ''
    if text:
        text_ = text.lower().split()
    # получаем подпись к фото
    if message.caption:
        text_ = message.caption.lower().split()
    # Проверяем если ли юзер в БД, если нет добавляем его
    await rq.check_chat_user(message)
    # если нет текста сообщения или подписи к фото
    if not text and not message.caption:
        return
    # иначе проверяем отправленное сообщение на список слов
    else:
        # список плохих слов
        for banned_message in banned_messages:
            # Если в сообщении от пользователя есть запрещенное слово
            if banned_message.lower().replace(' ', '') in text_:
                await message.delete()
                # выделяем "плохое" слово в сообщении
                word = ''
                for w in text_:
                    if banned_message.lower().replace(' ', '') == w:
                        word = w
                # добавляем нарушение пользователю
                await rq.add_chat_action(user_id=message.from_user.id,
                                         type_='bad word')
                # проверяем наличие нарушений (и если количество превышает лимит совершаем заданное действие)
                await rq.check_violations(message=message, bot=bot, word_bad=word)
                return
        # список слов благодарности
        await word_of_gradit(message=message, text_=text_)


@router.message(IsGroup())
@router.message_reaction(IsGroup())
async def check_messages(message_reaction: MessageReactionUpdated, bot: Bot):
    """
    Обработка постановки реакции на сообщения в группе
    :param message_reaction:
    :param bot:
    :return:
    """
    logging.info('check_messages message_reaction')
    # если новая реакция
    if message_reaction.new_reaction:
        # проверка, что реакция '👍'
        if message_reaction.new_reaction[0].emoji == '👍':
            # получаем информацию о сообщении на которое поставили '👍'
            message_id: MessageId = await rq.select_message_id(message_id=message_reaction.message_id)
            if message_id:
                # if not message_id.message_thread_id:
                #     print('not message_id.message_thread_id:')
                #     return
                # если реакция поставлена на свое же сообщение
                if message_id.tg_id == message_reaction.user.id:
                    return
                helping_user = await rq.select_chat_user(message_id.tg_id)
                chat_user = await rq.select_chat_user(message_id.tg_id)
                await rq.add_total_help(helping_user.tg_id)
                await rq.add_reputation(user_id=helping_user.tg_id)
                await rq.add_chat_action(user_id=message_id.tg_id,
                                         type_='help boost')
                await rq.update_last_help_boost(message_id.tg_id)
                msg = await bot.send_message(chat_id=message_reaction.chat.id,
                                             text=f'👤 Пользователь <a href="tg://user?id={helping_user.tg_id}">'
                                                  f'{helping_user.user_name}</a>'
                                                  f' (репутация {helping_user.total_help}) '
                                                  f'помог в ЧАТЕ и '
                                                  f'заработал +1 к своему общему рейтингу',
                                             message_thread_id=message_id.message_thread_id)
                await asyncio.sleep(1 * 60)
                await msg.delete()
        if message_reaction.new_reaction[0].emoji == '👎':
            message_id: MessageId = await rq.select_message_id(message_id=message_reaction.message_id)
            if message_id:
                helping_user = await rq.select_chat_user(message_id.tg_id)
                chat_user = await rq.select_chat_user(message_id.tg_id)
                await rq.update_last_rep_boost(message_id.tg_id)
                await rq.remove_reputation(message_id.tg_id)
                await rq.add_chat_action(user_id=message_id.tg_id,
                                         type_='rep unboost')
                msg = await bot.send_message(chat_id=message_reaction.chat.id,
                                             text=f'👤 Пользователь {message_reaction.user.full_name} '
                                                  f'поставил 👎 пользователю {chat_user.first_name} {chat_user.last_name}'
                                                  f' (репутация {helping_user.total_help}) и '
                                                  f'понизил его репу на -1',
                                             message_thread_id=message_id.message_thread_id)
                await asyncio.sleep(1 * 60)
                await msg.delete()
