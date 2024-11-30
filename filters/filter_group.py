import logging

from aiogram.enums.chat_member_status import ChatMemberStatus
from aiogram.types import Message
from aiogram import Bot
from datetime import datetime, timedelta
import re


async def is_admin(message: Message, bot: Bot):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    bot = await bot.get_chat_member(message.chat.id, bot.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR] or\
            bot.status != ChatMemberStatus.ADMINISTRATOR:
        return False
    return True


async def is_admin_bot_in_group(message: Message, bot: Bot) -> bool:
    logging.info('is_admin_bot_in_group')
    bot = await bot.get_chat_member(chat_id=message.chat.id, user_id=bot.id)
    if bot.status != ChatMemberStatus.ADMINISTRATOR:
        return False
    return True


def parse_time(time: str | None):
    if not time:
        return None

    re_match = re.match(r"(\d+)([a-z])", time.lower().strip())
    now_datetime = datetime.now()

    if re_match:
        value = int(re_match.group(1))
        unit = re_match.group(2)

        match unit:
            case "h":
                time_delta = timedelta(hours=value)
            case "d":
                time_delta = timedelta(days=value)
            case "w":
                time_delta = timedelta(weeks=value)
            case _:
                return None
    else:
        return None

    new_datetime = now_datetime + time_delta
    return new_datetime
