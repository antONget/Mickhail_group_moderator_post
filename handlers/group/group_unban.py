from aiogram.types import Message
from aiogram.filters import Command, CommandObject, or_f
from aiogram import Bot, Router

from database import requests as rq
from database.models import ChatUser
from filters.admin_chat import IsAdminCheck, IsAdminChat
from filters.groups_chat import IsGroup
from utils.error_handling import error_handler

import logging
import asyncio

router = Router()


@router.message(IsGroup(),
                Command('unban', prefix="!"),
                IsAdminChat())
@error_handler
async def into_command_unban_user(message: Message, bot: Bot, command: CommandObject):
    """
    Команда /unban доступна только администраторам проекта и группы
    :param message:
    :param command:
    :param bot:
    :return:
    """
    logging.info('into_command_unban_user')
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)  # Удаление сообщения
    if not message.reply_to_message:
        await message.answer('Для применения команды unban требуется ответить на сообщение пользователя')
        return
    try:
        user_id = message.reply_to_message.from_user.id
        await bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
        # если удалось получить ID пользователя
        if user_id:
            msg = await message.answer(f"Администратор <a href='tg://user?id={message.from_user.id}'>"
                                       f"{message.from_user.full_name}</a>\n"
                                       f"📣 Разблокировал <a href='tg://user?id={user_id}'>"
                                       f"{message.reply_to_message.from_user.username}</a>\n")
            await asyncio.sleep(5)
            await msg.delete()

        else:
            msg = await message.reply("Пользователь не найден.")
            await asyncio.sleep(5)
            await msg.delete()
    except Exception as e:
        msg = await message.reply(f"Не удалось забанить пользователя. Ошибка: {e}")
        await asyncio.sleep(5)
        await msg.delete()


@router.message(IsGroup(),
                Command('unban', prefix="!"))
@error_handler
async def into_command_unban_user(message: Message,  bot: Bot):
    """
    Команда /unban доступна только администраторам проекта и группы
    :param message:
    :param bot:
    :return:
    """
    logging.info('into_command_unban_user')
    msg = await message.answer(text='Команду !unban может применять только администратор проекта или группы')
    await asyncio.sleep(5)
    await msg.delete()
