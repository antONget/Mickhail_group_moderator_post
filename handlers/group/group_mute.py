from aiogram import Router, Bot
from aiogram.filters import Command, or_f
from aiogram.types import Message, ChatPermissions
from aiogram.exceptions import TelegramBadRequest

from filters.admin_chat import IsAdminCheck, IsAdminChat
from filters.groups_chat import IsGroup
from config_data.config import Config, load_config
from utils.error_handling import error_handler

import logging
import asyncio
import datetime
import re

config: Config = load_config()
router = Router()


@router.message(IsGroup(),
                Command('mute', prefix="!"),
                IsAdminChat())
@error_handler
async def mute_chat_member(message: Message, bot: Bot):
    logging.info(f'mute_chat_member')
    if message.reply_to_message:
        member_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id
        only_read_permissions = ChatPermissions(can_send_messages=False,
                                                can_send_media_messages=False,
                                                can_send_polls=False,
                                                can_send_other_messages=False,
                                                can_add_web_page_previews=False,
                                                can_change_info=False,
                                                can_invite_users=False,
                                                can_pin_messages=False)
        # Это регулярное выражение используется для поиска и сопоставления строки, которая начинается с "(!mute)".
        # За которым может следовать опциональный числовой аргумент (\d+), а затем также может следовать опциональное
        # текстовое (буквенное) значение ([a-zA-Zа-яА-Я ]+).
        command = re.compile(r"(!mute) ?(\d+)? ?([a-zA-Zа-яА-Я ]+)?").match(message.text)
        time = command.group(2)
        comment = command.group(3)
        if not time:
            time = 30
        else:
            time = int(time)
        until_date = datetime.datetime.now() + datetime.timedelta(minutes=time)
        try:
            await bot.restrict_chat_member(chat_id=chat_id,
                                           user_id=member_id,
                                           permissions=only_read_permissions,
                                           until_date=until_date)
            await message.reply(f'🔇 {message.reply_to_message.from_user.full_name}'
                                f' был ограничен отправлять сообщения на {time} минут.\n'
                                f'💬 Причина {comment}')
        except TelegramBadRequest:
            await message.reply(f'🚫 Этому пользователю нельзя ограничить возможность отправки сообщений!')
    else:
        msg = await message.reply(f'❌ Эта команда работает только в ответ на сообщение!')
        await asyncio.sleep(5)
        await msg.delete()


@router.message(IsGroup(),
                Command('unmute', prefix='!'),
                or_f(IsAdminCheck(),
                IsAdminChat()))
@error_handler
async def unmute_chat_member(message: Message, bot: Bot):
    logging.info(f'unmute_chat_member')
    if message.reply_to_message:
        member_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id
        chat_permission = (await bot.get_chat(message.chat.id)).permissions
        try:
            await bot.restrict_chat_member(chat_id=chat_id,
                                           user_id=member_id,
                                           permissions=chat_permission,
                                           until_date=datetime.datetime.now())
            await message.reply(f'👤 {message.from_user.full_name}'
                                f' размутил {message.reply_to_message.from_user.full_name}\n')
        except TelegramBadRequest:
            await message.reply('f🚫 Этого пользователя нельзя размутить!')
    else:
        msg = await message.reply(f'❌ Эта команда работает только в ответ на сообщение!')
        await asyncio.sleep(15)
        await msg.delete()


@router.message(IsGroup(),
                or_f(Command('mute', prefix="!"),
                     Command('unmute', prefix="!")))
@error_handler
async def into_command_ban_user(message: Message,  bot: Bot):
    """
    Команда mute/unmute доступна только администраторам проекта и группы
    :param message:
    :param bot:
    :return:
    """
    logging.info('into_command_ban_user')
    msg = await message.answer(text='Команду может применять только администратор проекта или группы')
    await asyncio.sleep(5)
    await msg.delete()
