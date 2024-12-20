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
    logging.info(f'check_messages {message.message_thread_id} {message.chat.id} {message.from_user.id}')
    if message.message_thread_id == 3:#67830:
        orders = await rq.select_order_status(status=rq.OrderStatus.publish)
        if message.reply_to_message.message_id:
            message_publish = []
            for order_message in orders:
                message_publish.append(int(order_message.chat_message.split('!')[0]))
            if message.reply_to_message.message_id not in message_publish:
                await message.delete()
                msg = await message.answer(
                    text='В этом разделе можно публиковать посты только через бота @MyderatorGroupsBot.\n'
                         'Оставьте вашу заявку в боте, мы ее рассмотрим и опубликуем!')
                await asyncio.sleep(10)
                await msg.delete()
                return
            else:
                return
        if message.from_user.id not in [7727341378, 1492644981, 1572221921, 843554518]:
            await message.delete()
            msg = await message.answer(text='В этом разделе можно публиковать посты только через бота @MyderatorGroupsBot.\n'
                                            'Оставьте вашу заявку в боте, мы ее рассмотрим и опубликуем!')
            await asyncio.sleep(10)
            await msg.delete()
    await rq.update_message_id(tg_id=message.from_user.id,
                               message_id=message.message_id,
                               message_thread_id=message.message_thread_id)
    text = message.text
    if text:
        text_ = text.lower().split()
    if message.caption:
        text_ = message.caption.lower().split()
    await rq.check_chat_user(message)  # Проверяем если ли юзер в БД, если нет добавляем его
    if not text and not message.caption:
        return


    # if message.entities:
        # for entity in message.entities:
        #     if entity.type in ['url', 'text_link']:
        #         await message.delete()
        #         # Добавляем нарушение
        #         await rq.add_chat_action(user_id=message.from_user.id,
        #                                  type_='ads')
        #         if not IsAdminChat:
        #             await rq.check_violations(message=message, bot=bot)  # Проверяем наличие нарушений
        #         break
    else:
        for banned_message in banned_messages:
            # Если в сообщении от пользователя есть запрещенное слово
            if banned_message.lower().replace(' ', '') in text_:
                await message.delete()
                for w in text_:
                    if banned_message.lower().replace(' ', '') == w:
                        word = w
                # Добавляем нарушение
                await rq.add_chat_action(user_id=message.from_user.id,
                                         type_='bad word')
                await rq.check_violations(message=message, bot=bot, word_bad=word)  # Проверяем наличие нарушений
                return
        # else:
        await word_of_gradit(message=message, text_=text_)
        # Если кто-то сказал спасибо
        # for word_of_gratitude in words_of_gratitude:
        #     if word_of_gratitude.lower().replace(' ', '') in text_:
        #         if message.reply_to_message:
        #             if message.reply_to_message.from_user.id == message.from_user.id:
        #                 await message.reply('👮‍♂ Даже не пытайся накрутить себе хорошую статистику')
        #             else:
        #                 chat_user = await rq.select_chat_user(message.from_user.id)
        #                 if chat_user:
        #                     # if chat_user.last_help_boost <= datetime.datetime.now() - datetime.timedelta(hours=float(config.tg_bot.time_of_help)):
        #                     helping_user = await rq.select_chat_user(message.reply_to_message.from_user.id)
        #                     chat_user = await rq.select_chat_user(message.from_user.id)
        #                     await rq.add_total_help(helping_user.tg_id)
        #                     await rq.add_reputation(user_id=helping_user.tg_id)
        #                     await rq.add_chat_action(user_id=message.from_user.id,
        #                                              type_='help boost')
        #                     await rq.update_last_help_boost(message.from_user.id)
        #                     await message.reply(f'👤 {message.reply_to_message.from_user.full_name}'
        #                                         f' ({helping_user.total_help} помощи)\n'
        #                                         f'помог {message.from_user.full_name} ({chat_user.total_help}'
        #                                         f' помощи) и получает +1 в свой рейтинг.')
        #                     # else:
        #                     #     await message.reply(f'🚫 Вы не можете сказать сказать слова благодарности'
        #                     #                         f' ещё {str(datetime.datetime.now() + datetime.timedelta(hours=float(config.tg_bot.time_of_help)) - chat_user.last_help_boost).split(".")[0]}')


@router.message(IsGroup())
@router.message_reaction(IsGroup())
async def check_messages(message_reaction: MessageReactionUpdated, bot: Bot):
    if message_reaction.new_reaction:
        if message_reaction.new_reaction[0].emoji == '👍':
            message_id: MessageId = await rq.select_message_id(message_id=message_reaction.message_id)
            if message_id:
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
                await bot.send_message(chat_id=message_reaction.chat.id,
                                       text=f'👤 Пользователь {chat_user.first_name} {chat_user.last_name}'
                                            f' (репутация {helping_user.total_help}) '
                                            f'помог пользователю {message_reaction.user.full_name} и '
                                            f'заработал +1 к своей репе',
                                       message_thread_id=message_id.message_thread_id)
        if message_reaction.new_reaction[0].emoji == '👎':
            message_id: MessageId = await rq.select_message_id(message_id=message_reaction.message_id)
            if message_id:
                helping_user = await rq.select_chat_user(message_id.tg_id)
                chat_user = await rq.select_chat_user(message_id.tg_id)
                await rq.update_last_rep_boost(message_id.tg_id)
                await rq.remove_reputation(message_id.tg_id)
                await rq.add_chat_action(user_id=message_id.tg_id,
                                         type_='rep unboost')
                await bot.send_message(chat_id=message_reaction.chat.id,
                                       text=f'👤 Пользователь {message_reaction.user.full_name} '
                                            f'поставил 👎 пользователю {chat_user.first_name} {chat_user.last_name}'
                                            f' (репутация {helping_user.total_help}) и '
                                            f'понизил его репу на -1',
                                       message_thread_id=message_id.message_thread_id)