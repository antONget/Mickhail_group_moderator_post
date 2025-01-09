from aiogram import Router, Bot
from aiogram.filters import Command, CommandObject
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
    """
    Выводит информацию о пользователе вызвавшего команду, если применить команду как ответную то получим информацию
     о пользователе на чье сообщение отвечаем
    :param message:
    :param bot:
    :return:
    """
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


@router.message(IsGroup(),
                Command('info_top', prefix='!'))
async def command_info_top(message: Message, command: CommandObject, bot: Bot):
    """
    Выводит список количества репутации у пользователей в порядке убывания, если передать через пробел число,
     то список ограничится только этим числом
    :param message:
    :param command:
    :param bot:
    :return:
    """
    logging.info(f'command_info_top')
    if not command.args:
        top = 10
    else:
        top_arg = command.args
        try:
            top = int(top_arg)
        except:
            await message.answer(text='Некорректно указано число пользователей')
            return
    list_users = await rq.select_chat_actions_top()
    if len(list_users) >= top:
        text = f'<b>Список TOP - {top}</b>\n\n'
        i = 0
        for user in list_users[:top]:
            i += 1
            text += f'{i}. <a href="tg://user?id={user.tg_id}">{user.user_name}</a> - {user.reputation}\n'
        await message.answer(text=text)
    else:
        await message.answer(text='Слишком большое число')
