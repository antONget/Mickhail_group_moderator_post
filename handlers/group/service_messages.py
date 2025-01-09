from aiogram.types import ChatMemberUpdated
from aiogram import Router, F, Bot

from database.requests import add_chat_user, update_status
from config_data.config import Config, load_config


import logging
import datetime

router = Router()
config: Config = load_config()


@router.chat_member(F.new_chat_member)
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    logging.info(f'on_user_join {event.new_chat_member.status} {event}')
    if event.new_chat_member.status == 'member':
        await add_chat_user(tg_id=event.from_user.id,
                            first_name=event.from_user.first_name,
                            last_name=event.from_user.last_name,
                            user_name=event.from_user.username,
                            status='active',
                            reputation=0,
                            total_help=0,
                            mutes=0,
                            last_rep_boost=datetime.datetime.now() - datetime.timedelta(hours=4),
                            last_help_boost=datetime.datetime.now() - datetime.timedelta(hours=4))
        await bot.send_message(chat_id=config.tg_bot.general_group,
                               text=f'Привет  @{event.new_chat_member.user.username},'
                                    f' почитай <a href="https://t.me/c/1327075982/69073/69075">правила группы</a>!',
                               message_thread_id=67828)
    elif event.new_chat_member.status == 'left':
        await update_status(user_id=event.from_user.id, status='left')
