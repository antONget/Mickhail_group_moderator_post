from database import requests as rq
from config_data.config import words_of_gratitude
from aiogram.types import Message
import logging
import asyncio
from database.models import MessageId
from config_data.config import Config, load_config

config: Config = load_config()


async def word_of_gradit(message: Message, text_: list):
    """
    Обработка благодарственных слов в тексте сообщений или в подписи к фотографии
    :param message:
    :param text_:
    :return:
    """
    logging.info(f'word_of_gradit {message.from_user.id}')
    if message.message_thread_id == 67830:
        return
    text_str = ''.join(text_)
    # проходим по всем словам благодарности из списка
    for word_of_gratitude in words_of_gratitude:
        # поиск слов благодарности в сообщении
        if word_of_gratitude.lower().replace(' ', '') in text_str:
            # если апдейт это не ответ на сообщение и не ответ на фото и не ответ на документ, то игнорируем
            if not message.reply_to_message.text and not message.reply_to_message.photo and\
                    not bool(message.reply_to_message.document):
                return
            # иначе если пользователь ответил на сове же сообщение
            elif message.reply_to_message.from_user.id == message.from_user.id:
                msg = await message.answer('👮‍♂ Даже не пытайся накрутить себе хорошую статистику')
                await asyncio.sleep(1 * 60)
                await msg.delete()
                return
            # иначе получаем id пользователя на чье сообщение ответили
            else:
                user_plus = message.reply_to_message.from_user.id
                # если действие совершено в топике с комментариями
                if message.message_thread_id == int(config.tg_bot.comment_topic):
                    message_replay = message.reply_to_message.message_id
                    message_user: MessageId = await rq.select_message_id(message_id=message_replay)
                    user_plus = message_user.tg_id
            # если сообщение является ответным
            if message.reply_to_message:
                # получаем информацию о том кто написал сообщение
                chat_user = await rq.select_chat_user(message.from_user.id)
                if chat_user:
                    # получаем информацию на чье сообщение ответили
                    helping_user = await rq.select_chat_user(user_plus)
                    await rq.add_total_help(helping_user.tg_id)
                    await rq.add_reputation(user_id=helping_user.tg_id)
                    await rq.add_chat_action(user_id=message.from_user.id,
                                             type_='help boost')
                    await rq.update_last_help_boost(message.from_user.id)
                    msg = await message.reply(f'👤 Пользователь <a href="tg://user?id={helping_user.tg_id}">'
                                              f'{helping_user.user_name}</a>'
                                              f' (репутация {helping_user.total_help}) '
                                              f'помог в ЧАТЕ и '
                                              f'заработал +1 к своему общему рейтингу')
                    await asyncio.sleep(1 * 60)
                    await msg.delete()
