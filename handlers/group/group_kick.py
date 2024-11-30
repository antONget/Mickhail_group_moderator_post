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
    user_identifier = 0
    if not command.args:
        await message.answer('Для применения команды kick требуется указать к кому и по какой причине она применяется')
        return
    args: list = command.args.split(" ", 1)
    # если указаны параметры к команде
    if args:
        # пользователь
        user_identifier = args[0]
        # если не указан пользователь или команда не была ответной на сообщение пользователя
        if not user_identifier and not message.reply_to_message:
            msg = await message.answer("Кого удалять? Ответьте на сообщение, укажите @username или ID пользователя.")
            await asyncio.sleep(5)
            await msg.delete()
            return
        elif not len(args) == 2:
            msg = await message.answer("Укажите причину kick")
            await asyncio.sleep(5)
            await msg.delete()
            return
    try:
        # если пользователь указан
        if user_identifier:
            # пытаемся получить ID пользователя
            try:
                user_id = int(user_identifier)
            except ValueError:
                user: ChatUser = await rq.select_chat_user_username(username=user_identifier.replace("@", ""))
                if user:
                    user_id = user.tg_id
                else:
                    msg = await message.reply("Пользователь c таким username не найден в БД, попробуйте применить"
                                              " команду использую ID пользователя")
                    await asyncio.sleep(5)
                    await msg.delete()
                    return
        # ответ на сообщение
        else:
            user_id: int = message.reply_to_message.from_user.id
            user: ChatUser = await rq.select_chat_user(tg_id=user_id)
        # если удалось получить ID пользователя
        if user_id:
            msg = await message.answer(f"Администратор <a href='tg://user?id={message.from_user.id}'>"
                                       f"{message.from_user.full_name}</a>\n"
                                       f"❌ Удалил <a href='tg://user?id={user_id}'>"
                                       f"{user.user_name}</a>\n"
                                       f"💬 По причине: {args[1]}")
            await bot.ban_chat_member(chat_id=message.chat.id, user_id=user_id)
            await asyncio.sleep(5)
            await bot.unban_chat_member(chat_id=message.chat.id, user_id=user_id)
            await msg.delete()

        else:
            msg = await message.reply("Пользователь не найден.")
            await asyncio.sleep(5)
            await msg.delete()
    except Exception as e:
        msg = await message.reply(f"Не удалось удалить пользователя. Ошибка: {e}")
        await asyncio.sleep(5)
        await msg.delete()


    # await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)  # Удаление сообщения
    # user_identifier = 0
    # if not command.args:
    #     await message.answer('Для применения команды kick требуется указать к кому и по какой причине она применяется')
    #     return
    # args: list = command.args.split(" ", 1)
    # if args:
    #     user_identifier = args[0]
    #     if not user_identifier and not message.reply_to_message:
    #         await message.answer("Кого удалять? Ответьте на сообщение, укажите @username или ID пользователя.")
    #         return
    #     reason_: str = " ".join(args[0:]) if len(args) > 1 else ""
    #     reason: str = " ".join(args[1:]) if len(args) > 1 else ""
    #     if not reason and not message.reply_to_message.from_user.id:
    #         await message.answer("Укажите причину kick")
    #         return
    #     else:
    #         reason = reason_
    # try:
    #     user = 0
    #     if user_identifier:
    #         try:
    #             user_id = int(user_identifier)
    #         except ValueError:
    #             user = await rq.get_user_username(username=user_identifier.replace("@", ""))
    #             if user:
    #                 user_id = user.tg_id
    #             else:
    #                 await message.reply("Пользователь c таким username не найден в БД, попробуйте применить"
    #                                     " команду использую ID пользователя")
    #                 return
    #     else:
    #         user_id = message.reply_to_message.from_user.id
    #         user = await rq.get_user(tg_id=user_id)
    #     if user_id:
    #         await message.answer(
    #             text=f"Администратор <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>"
    #                  f" кикнул <a href='tg://user?id={user_id}'>{user.username}</a> по причине: {reason}")
    #
    #     else:
    #         await message.answer("Пользователь не найден.")
    # except Exception as e:
    #     await message.answer(f"Не удалось кикнуть пользователя")


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