from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject, or_f

from utils.error_handling import error_handler
from filters.admin_chat import IsAdminCheck, IsAdminChat
from filters.groups_chat import IsGroup
from database import requests as rq
from database.models import ChatUser

import logging
import asyncio

router = Router()


@router.message(IsGroup(),
                Command('kick', prefix="!"),
                IsAdminChat())
@error_handler
async def into_command_kick_user(message: Message, command: CommandObject, bot: Bot):
    """
    Команда /kick доступна только администраторам проекта и группы
    :param message:
    :param command:
    :param bot:
    :return:
    """
    logging.info('into_command_kick_user')
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)  # Удаление сообщения
    if not message.reply_to_message:
        await message.answer('Для применения команды kick требуется ответить на сообщение пользователя')
        return
    if not command.args:
        await message.answer('Для применения команды kick требуется указать к кому и по какой причине она применяется')
        return
    try:
        reason = command.args
        user_id = message.reply_to_message.from_user.id
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
        await asyncio.sleep(5)
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
        msg = await message.answer(
            text=f"Администратор <a href='tg://user?id={message.from_user.id}'>{message.from_user.username}</a>"
                 f" кикнул <a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.username}</a>"
                 f" по причине: {reason}")
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as e:
        await message.answer(f"Не удалось кикнуть пользователя {e}")


@router.message(IsGroup(),
                Command('kick', prefix="!"))
@error_handler
async def into_command_kick_user(message: Message,  bot: Bot):
    """
    Команда /kick доступна только администраторам проекта и группы
    :param message:
    :param bot:
    :return:
    """
    logging.info('into_command_kick_user')
    msg = await message.answer(text='Команду !kick может применять только администратор проекта или группы')
    await asyncio.sleep(5)
    await msg.delete()