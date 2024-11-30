from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject, or_f

from filters.admin_chat import IsAdminCheck, IsAdminChat
from filters.groups_chat import IsGroup
from database import requests as rq
from database.models import ChatUser
from utils.error_handling import error_handler

import logging
import asyncio

router = Router()


@router.message(IsGroup(),
                Command('ban', prefix="!"),
                IsAdminChat())
@error_handler
async def into_command_ban_user(message: Message, command: CommandObject, bot: Bot):
    """
    Команда /ban доступна только администраторам проекта и группы
    :param message:
    :param command:
    :param bot:
    :return:
    """
    logging.info('into_command_ban_user')
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)  # Удаление сообщения
    if not message.reply_to_message:
        await message.answer('Для применения команды ban требуется ответить на сообщение пользователя')
        return
    if not command.args:
        await message.answer('Для применения команды ban требуется указать к кому и по какой причине она применяется')
        return
    try:
        reason = command.args
        user_id = message.reply_to_message.from_user.id
    # user_identifier = 0
    # if not command.args:
    #     await message.answer('Для применения команды !ban требуется указать к кому и по какой причине она применяется')
    #     return
    # args: list = command.args.split(" ", 1)
    # # если указаны параметры к команде
    # if args:
    #     # пользователь
    #     user_identifier: str = args[0]
    #     # если не указан пользователь или команда не была ответной на сообщение пользователя
    #     if not user_identifier and not message.reply_to_message:
    #         msg = await message.answer("Кого банить? Ответьте на сообщение или укажите @username (ID пользователя).")
    #         await asyncio.sleep(5)
    #         await msg.delete()
    #         return
    #     if not len(args) == 2:
    #         msg = await message.answer("Укажите причину ban")
    #         await asyncio.sleep(5)
    #         await msg.delete()
    #         return
    #
    # try:
    #     # если пользователь указан
    #     if user_identifier:
    #         # пытаемся получить ID пользователя
    #         try:
    #             user_id = int(user_identifier)
    #         except ValueError:
    #             user: ChatUser = await rq.select_chat_user_username(username=user_identifier.replace("@", ""))
    #             if user:
    #                 user_id: int = user.tg_id
    #             else:
    #                 msg = await message.reply("Пользователь c таким username не найден в БД, попробуйте применить"
    #                                           " команду использую ID пользователя")
    #                 await asyncio.sleep(5)
    #                 await msg.delete()
    #                 return
    #     # ответ на сообщение
    #     else:
    #         user_id: int = message.reply_to_message.from_user.id
    #     user: ChatUser = await rq.select_chat_user(tg_id=user_id)
        # если удалось получить ID пользователя
        await bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
        msg = await message.answer(f"Администратор <a href='tg://user?id={message.from_user.id}'>"
                                   f"{message.from_user.username}</a>\n"
                                   f"🚫 Заблокировал <a href='tg://user?id={user_id}'>"
                                   f"{message.reply_to_message.from_user.username}</a>\n"
                                   f"💬 По причине: {reason}")
        await asyncio.sleep(5)
        await msg.delete()
        #
        # else:
        #     msg = await message.reply("Пользователь не найден.")
        #     await asyncio.sleep(5)
        #     await msg.delete()
    except Exception as e:
        msg = await message.reply(f"Не удалось забанить пользователя. Ошибка: {e}")
        await asyncio.sleep(5)
        await msg.delete()


@router.message(IsGroup(),
                Command('ban', prefix="!"))
@error_handler
async def into_command_ban_user(message: Message,  bot: Bot):
    """
    Команда /ban доступна только администраторам проекта и группы
    :param message:
    :param bot:
    :return:
    """
    logging.info('into_command_ban_user')
    msg = await message.answer(text='Команду !ban может применять только администратор проекта или группы')
    await asyncio.sleep(5)
    await msg.delete()
