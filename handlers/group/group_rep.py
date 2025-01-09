from aiogram import Router, Bot, F
from aiogram.types import Message

from filters.groups_chat import IsGroup
from database import requests as rq
from config_data.config import Config, load_config

import logging
import asyncio
import datetime

config: Config = load_config()
router = Router()


@router.message(IsGroup(),
                F.text.endswith('rep'))
async def check_messages(message: Message, bot: Bot):
    """
    Увеличение/уменьшение репутации пользователю на чье сообщение ответили
    :param message:
    :param bot:
    :return:
    """
    logging.info(f'check_messages')
    await rq.check_chat_user(message)  # Проверяем если ли юзер в БД, если нет добавляем его
    if message.html_text == '+rep':
        if message.reply_to_message.text:
            if message.reply_to_message.from_user.id == message.from_user.id:
                await message.reply('🚫 Ты не можешь повысить репутацию сам себе.')
            else:
                chat_user = await rq.select_chat_user(message.from_user.id)
                rep_boost_user = await rq.select_chat_user(message.reply_to_message.from_user.id)
                if chat_user.last_rep_boost <= datetime.datetime.now() - datetime.timedelta(hours=float(config.tg_bot.time_of_rep)):
                    await rq.update_last_rep_boost(message.from_user.id)
                    await rq.add_reputation(message.reply_to_message.from_user.id)
                    await rq.add_chat_action(user_id=message.from_user.id,
                                             type_='rep boost')
                    await message.reply(f'👤 {message.from_user.full_name}'
                                        f' ({chat_user.reputation} репутации) поднял репутацию '
                                        f'{message.reply_to_message.from_user.full_name}'
                                        f' ({rep_boost_user.reputation} + 1 репутации).')
                else:
                    await message.reply(f'🚫 Вы не можете поднимать репутацию еще'
                                        f' {str(chat_user.last_rep_boost - datetime.datetime.now() + datetime.timedelta(hours=float(config.tg_bot.time_of_rep))).split(".")[0]} часов.')

        else:
            msg = await message.reply(f'❌ Эта команда работает только в ответ на сообщение!')
            await asyncio.sleep(5)
            await msg.delete()
    elif message.html_text == '-rep':
        if message.reply_to_message.text:
            if message.reply_to_message.from_user.id == message.from_user.id:
                await message.reply('🚫 Ты не можешь понижать репутацию сам себе.')
            else:
                chat_user = await rq.select_chat_user(message.from_user.id)
                rep_boost_user = await rq.select_chat_user(message.reply_to_message.from_user.id)
                if chat_user.last_rep_boost <= datetime.datetime.now() - datetime.timedelta(hours=float(config.tg_bot.time_of_rep)):
                    await rq.update_last_rep_boost(message.from_user.id)
                    await rq.remove_reputation(message.reply_to_message.from_user.id)
                    await rq.add_chat_action(user_id=message.from_user.id,
                                             type_='rep unboost')
                    await message.reply(f'👤 {message.from_user.full_name} ({chat_user.reputation}'
                                        f' репутации) понизил репутацию '
                                        f'{message.reply_to_message.from_user.full_name}'
                                        f' ({rep_boost_user.reputation} - 1 репутации).')

                else:
                    await message.reply(f'🚫 Вы не можете понижать репутацию еще {str(chat_user.last_rep_boost - datetime.datetime.now() + datetime.timedelta(hours=float(config.tg_bot.time_of_rep))).split(".")[0]} часов.')

        else:
            msg = await message.reply(f'❌ Эта команда работает только в ответ на сообщение!')
            await asyncio.sleep(5)
            await msg.delete()
