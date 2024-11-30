import asyncio
import logging

from aiogram import Router, Bot
from aiogram.filters import Command, or_f
from aiogram.types import Message

from filters.admin_chat import IsAdminCheck, IsAdminChat
from filters.groups_chat import IsGroup
from utils.error_handling import error_handler
from filters.filter_group import is_admin_bot_in_group
from filters.admin_filter import check_super_admin
from database import requests as rq

router = Router()


@router.message(IsGroup(),
                Command('set_group', prefix="!"),
                or_f(IsAdminCheck(),
                IsAdminChat()))
@error_handler
async def process_add_group(message: Message, bot: Bot):
    logging.info('process_add_group')
    chat_id = message.chat.id
    await message.delete()
    await rq.update_group(peer_id=chat_id)
    msg = await message.answer(text='Группа установлена как основная')
    await asyncio.sleep(5)
    await msg.delete()
