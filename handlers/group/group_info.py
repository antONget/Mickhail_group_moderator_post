from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from filters.groups_chat import IsGroup
from database import requests as rq
from config_data.config import Config, load_config

import logging

config: Config = load_config()
router = Router()


@router.message(IsGroup(),
                Command('info', prefix='!'))
async def command_info(message: Message, bot: Bot):
    logging.info(f'command_info')
    await rq.check_chat_user(message)  # Проверяем если ли юзер в БД, если нет добавляем его
    if not message.reply_to_message:
        logging.info(f'command_info not-replay')
        chat_user = await rq.select_chat_user(message.from_user.id)
        count_violations = await rq.count_user_violations(user_id=message.from_user.id,
                                                          hours=(24 * 30))
        await message.reply(f'📊 Статистика {message.from_user.full_name}\n'
                            f'👤 Репутация: {chat_user.reputation}\n'
                            f'🚑 Всего помощи: {chat_user.total_help}\n'
                            f'🔇 Кол-во мутов: {chat_user.mutes}\n'
                            f'🚫 Кол-во нарушений за последние 30 дней: {count_violations}')
    else:
        logging.info(f'command_info replay')
        chat_user = await rq.select_chat_user(message.reply_to_message.from_user.id)
        count_violations = await rq.count_user_violations(message.reply_to_message.from_user.id, hours=(24 * 30))
        await message.reply(f'📊 Статистика {message.reply_to_message.from_user.full_name}\n'
                            f'👤 Репутация: {chat_user.reputation}\n'
                            f'🚑 Всего помощи: {chat_user.total_help}\n'
                            f'🔇 Кол-во мутов: {chat_user.mutes}\n'
                            f'🚫 Кол-во нарушений за последние 30 дней: {count_violations}')
