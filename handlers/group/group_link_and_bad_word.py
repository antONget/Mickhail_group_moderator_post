from aiogram import Router, Bot
from aiogram.types import Message

from filters.admin_chat import IsAdminChat
from filters.groups_chat import IsGroup
from config_data.config import banned_messages, words_of_gratitude
from database import requests as rq
from config_data.config import Config, load_config

import logging
import datetime

config: Config = load_config()
router = Router()


@router.message(IsGroup())
async def check_messages(message: Message, bot: Bot):
    logging.info(f'check_messages {message.message_thread_id} {message.chat.id}')
    text = message.text
    if not text:
        await message.delete()
        return
    await rq.check_chat_user(message)  # Проверяем если ли юзер в БД, если нет добавляем его

    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link']:
                await message.delete()
                # Добавляем нарушение
                await rq.add_chat_action(user_id=message.from_user.id,
                                         type_='ads')
                if not IsAdminChat:
                    await rq.check_violations(message=message, bot=bot)  # Проверяем наличие нарушений
                break
    else:
        for banned_message in banned_messages:
            # Если в сообщении от пользователя есть запрещенное слово
            if banned_message.lower().replace(' ', '') in text.lower().replace(' ', ''):
                await message.delete()
                # Добавляем нарушение
                await rq.add_chat_action(user_id=message.from_user.id,
                                         type_='bad word')
                await rq.check_violations(message=message, bot=bot)  # Проверяем наличие нарушений
                break
        else:
            # Если кто-то сказал спасибо
            for word_of_gratitude in words_of_gratitude:
                if word_of_gratitude.lower().replace(' ', '') in text.lower().replace(' ', ''):
                    if message.reply_to_message:
                        if message.reply_to_message.from_user.id == message.from_user.id:
                            await message.reply('👮‍♂ Даже не пытайся накрутить себе хорошую статистику')
                        else:
                            chat_user = await rq.select_chat_user(message.from_user.id)
                            if chat_user.last_help_boost <= datetime.datetime.now() - datetime.timedelta(hours=float(config.tg_bot.time_of_help)):
                                helping_user = await rq.select_chat_user(message.reply_to_message.from_user.id)
                                chat_user = await rq.select_chat_user(message.from_user.id)
                                await rq.add_total_help(helping_user.tg_id)
                                await rq.add_reputation(user_id=helping_user.tg_id)
                                await rq.add_chat_action(user_id=message.from_user.id,
                                                         type_='help boost')
                                await rq.update_last_help_boost(message.from_user.id)
                                await message.reply(f'👤 {message.reply_to_message.from_user.full_name}'
                                                    f' ({helping_user.total_help} помощи)\n'
                                                    f'помог {message.from_user.full_name} ({chat_user.total_help}'
                                                    f' помощи) и получает +1 в свой рейтинг.')
                            else:
                                await message.reply(f'🚫 Вы не можете сказать сказать слова благодарности'
                                                    f' ещё {str(datetime.datetime.now() + datetime.timedelta(hours=float(config.tg_bot.time_of_help)) - chat_user.last_help_boost).split(".")[0]}')

