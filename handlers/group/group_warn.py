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
                Command('warn', prefix="!"),
                IsAdminChat())
@error_handler
async def into_command_kick_user(message: Message, command: CommandObject, bot: Bot):
    """
    Команда /warn доступна только администраторам проекта и группы
    :param message:
    :param command:
    :param bot:
    :return:
    """
    logging.info('into_command_kick_user')
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)  # Удаление сообщения
    if not message.reply_to_message:
        await message.answer('Для применения команды warn требуется ответить на сообщение пользователя')
        return
    if not command.args:
        await message.answer('Для применения команды warn требуется указать к кому и по какой причине она применяется')
        return
    try:
        reason = command.args
        user_id = message.reply_to_message.from_user.id
        # если удалось получить ID пользователя
        if user_id:
            # Добавляем нарушение
            await rq.add_chat_action(user_id=message.from_user.id,
                                     type_='warn')
            await rq.check_violations(message=message, bot=bot)  # Проверяем наличие нарушений
            msg = await message.answer(
                text=f"Администратор <a href='tg://user?id={message.from_user.id}'>{message.from_user.username}</a>"
                     f" предупредил <a href='tg://user?id={user_id}'>{message.reply_to_message.from_user.username}</a>"
                     f" по причине: {reason}")
            await asyncio.sleep(5)
            await msg.delete()
        else:
            msg = await message.reply("Пользователь не найден.")
            await asyncio.sleep(5)
            await msg.delete()
    except Exception as e:
        msg = await message.reply(f"Не удалось установить нарушение пользователю пользователя. Ошибка: {e}")
        await asyncio.sleep(5)
        await msg.delete()


@router.message(IsGroup(),
                Command('warn', prefix="!"))
@error_handler
async def into_command_warn_user(message: Message,  bot: Bot):
    """
    Команда /warn доступна только администраторам проекта и группы
    :param message:
    :param bot:
    :return:
    """
    logging.info('into_command_warn_user')
    msg = await message.answer(text='Команду !warn может применять только администратор проекта или группы')
    await asyncio.sleep(5)
    await msg.delete()