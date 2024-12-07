import logging
import datetime
from dataclasses import dataclass
from aiogram.types import Message, ChatPermissions
from database.models import async_session
from database.models import ChatUser, ChatAction, Group, Order, User
from sqlalchemy import select
from aiogram import Bot
from config_data.config import Config, load_config

from sqlalchemy import desc

config: Config = load_config()


# Добавляем пользователя из чата в БД
async def add_chat_user(tg_id: int, first_name: str, last_name: str, user_name: str, status: str, reputation: int,
                        total_help: int, mutes: int, last_rep_boost: datetime,  last_help_boost: datetime) -> None:
    logging.info(f'add_chat_user')
    async with async_session() as session:
        user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == tg_id))
        if not user:
            session.add(ChatUser(**{'tg_id': tg_id, 'first_name': first_name, 'last_name': last_name,
                                    'user_name': user_name, 'status': status, 'reputation': reputation,
                                    'total_help': total_help, 'mutes': mutes, 'last_rep_boost': last_rep_boost,
                                    'last_help_boost': last_help_boost}))
            await session.commit()


# Получаем чат юзера
async def select_chat_user(tg_id: int) -> ChatUser:
    logging.info(f'select_chat_user')
    async with async_session() as session:
        return await session.scalar(select(ChatUser).where(ChatUser.tg_id == tg_id))


# Получаем чат юзера
async def select_chat_user_username(username: str) -> ChatUser:
    """
    Получаем ChatUser по его user_name
    :param username:
    :return:
    """
    logging.info(f'select_chat_user_username')
    async with async_session() as session:
        return await session.scalar(select(ChatUser).where(ChatUser.user_name == username))


async def select_chat_actions(tg_id: int) -> list[ChatAction]:
    logging.info(f'select_chat_action')
    async with async_session() as session:
        chat_actions = await session.scalars(select(ChatAction).where(ChatAction.user_id == tg_id))
        list_chat_actions = [chat_action for chat_action in chat_actions]
        return list_chat_actions


# Проверяем есть ли юзер написавший сообщение в БД
async def check_chat_user(message: Message) -> None:
    logging.info(f'check_chat_user')
    if message.reply_to_message:
        # Если не удалось получить юзера из БД
        async with async_session() as session:
            user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == message.reply_to_message.from_user.id))
            if not user:
                # Пытаемся его добавить
                await add_chat_user(tg_id=message.reply_to_message.from_user.id,
                                    first_name=message.reply_to_message.from_user.first_name if message.reply_to_message.from_user.first_name else 'first_name',
                                    last_name=message.reply_to_message.from_user.last_name if message.reply_to_message.from_user.last_name else 'last_nmae',
                                    user_name=message.reply_to_message.from_user.username if message.reply_to_message.from_user.username else 'username',
                                    status='active',
                                    reputation=0,
                                    total_help=0,
                                    mutes=0,
                                    last_rep_boost=datetime.datetime.now() - datetime.timedelta(hours=4),
                                    last_help_boost=datetime.datetime.now() - datetime.timedelta(hours=4))

            else:
                if not user.user_name == message.reply_to_message.from_user.username:
                    if message.reply_to_message.from_user.username:
                        user.user_name = message.reply_to_message.from_user.username
                        await session.commit()

    else:
        # Если не удалось получить юзера из БД, то добавляем его
        async with async_session() as session:
            user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == message.from_user.id))
            if not user:
                await add_chat_user(tg_id=message.from_user.id,
                                    first_name=message.from_user.first_name,
                                    last_name=message.from_user.last_name,
                                    user_name=message.from_user.username,
                                    status='active',
                                    reputation=0,
                                    total_help=0,
                                    mutes=0,
                                    last_rep_boost=datetime.datetime.now() - datetime.timedelta(hours=4),
                                    last_help_boost=datetime.datetime.now() - datetime.timedelta(hours=4))
            else:
                if not user.user_name == message.from_user.username:
                    user.user_name = message.from_user.username
                    await session.commit()


# Количество нарушений юзера за последнее N-часов / Если 0 то за всё время
async def count_user_violations(user_id: int, hours: int = 0) -> int:
    logging.info(f'count_user_violations')
    async with async_session() as session:
        violations = (await session.scalars(select(ChatAction).where(ChatAction.user_id == user_id))).all()
    if hours <= 0:
        # Число нарушений за всё время
        count = 0
        for violation in violations:
            if violation.type in ['ads', 'bad word']:
                count += 1
        return count
    else:
        count = 0
        # Число нарушений за последнее N-часов
        for violation in violations:
            # Проходимся по всем нарушениям юзера и считаем все которые были нарушены менее N-часов назад
            if violation.added >= datetime.datetime.now() - datetime.timedelta(hours=hours):
                count = 0
                for violation in violations:
                    if violation.type in ['ads', 'bad word']:
                        count += 1
        return count


# Функция обновляет дату последнего поднятия или снятия репутации
async def update_last_rep_boost(user_id: int) -> None:
    logging.info(f'update_last_rep_boost')
    async with async_session() as session:
        chatUser = await session.scalar(select(ChatUser).where(ChatUser.tg_id == user_id))
        if chatUser:
            chatUser.last_rep_boost = datetime.datetime.now()
            await session.commit()


async def update_status(user_id: int, status: str) -> None:
    logging.info(f'update_status')
    async with async_session() as session:
        chat_user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == user_id))
        if chat_user:
            chat_user.status = status
            await session.commit()


# Функция, которая добавляет репутацию +rep
async def add_reputation(user_id: int):
    logging.info(f'update_last_rep_boost {user_id}')
    async with async_session() as session:
        chat_user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == user_id))
        logging.info(f'update_last_rep_boost {chat_user}')
        if chat_user:
            temp = chat_user.reputation
            chat_user.reputation = temp + 1
            await session.commit()


# Функция, которая добавляет репутацию +rep
async def remove_reputation(user_id: int):
    logging.info(f'update_last_rep_boost')
    async with async_session() as session:
        chat_user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == user_id))
        if chat_user:
            chat_user.reputation -= 1
            await session.commit()


# Добавляем действие из чата в БД
async def add_chat_action(user_id: int, type_: str):
    logging.info(f'update_last_rep_boost')
    async with async_session() as session:
        session.add(ChatAction(**{"user_id": user_id, "type": type_, "added": datetime.datetime.now()}))
        await session.commit()


# Функция добавляет рейтинг за помощь на +1
async def add_total_help(user_id: int):
    logging.info(f'add_total_help')
    async with async_session() as session:
        chat_user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == user_id))
        chat_user.total_help += 1
        await session.commit()


async def check_violations(message: Message, bot: Bot, word_bad: str = "***"):
    """
    Действия с нарушениями
    :param message:
    :param bot:
    :return:
    """
    logging.info(f'update_last_rep_boost')
    async with async_session() as session:
        violations = await session.scalars(select(ChatAction).where(ChatAction.user_id == message.from_user.id)) # Получаем все нарушения от юзера
    count_bad_words = 0
    count_advertising = 0
    count_warn = 0
    # Получаем каждое нарушение из списка
    for violation in violations:
        if violation.added >= datetime.datetime.now() - datetime.timedelta(minutes=int(config.tg_bot.time_of_violations)):
            if violation.type == 'bad word':  # Плохие слова
                count_bad_words += 1
            elif violation.type == 'ads':  # Реклама
                count_advertising += 1
            elif violation.type == 'warn':  # Реклама
                count_warn += 1
    OnlyReadPermissions = ChatPermissions(can_send_messages=False,
                                          can_send_media_messages=False,
                                          can_send_polls=False,
                                          can_send_other_messages=False,
                                          can_add_web_page_previews=False,
                                          can_change_info=False,
                                          can_invite_users=False,
                                          can_pin_messages=False)
    userChatActions = await select_chat_actions(tg_id=message.from_user.id)
    type = userChatActions[len(userChatActions) - 1].type
    if type == 'bad word':
        if count_bad_words > 0:  # Если количество плохих слов Больше 0
            if count_bad_words >= 5:  # Если количество плохих слов больше или равно 5
                until_date = datetime.datetime.now() + datetime.timedelta(hours=int(config.tg_bot.mute_by_bad_word_time))
                try:
                    await bot.restrict_chat_member(chat_id=message.chat.id,
                                                   user_id=message.from_user.id,
                                                   permissions=OnlyReadPermissions,
                                                   until_date=until_date)
                    return await message.answer(f'👤{message.from_user.full_name} '
                                                f'был ограничен в возможности отправлять сообщения '
                                                f'на {config.tg_bot.mute_by_bad_word_time} час.\n'
                                                f'📩Причина: Плохие слова в чате.')
                except:
                    await bot.send_message(chat_id=config.tg_bot.support_id,
                                           text=f'Не удалось заблокироать {message.from_user.id}/{message.from_user.username} по причине плохих слов')
            else:
                return await message.answer(f'🔍 Замечено плохое слово - {word_bad}\n'
                                            f'👤 Его написал {message.from_user.full_name}\n'
                                            f'🤬 Предупреждение № {count_bad_words}\n')
    elif type == 'ads':
        if count_advertising > 0:  # Если количество рекламных ссылок больше 0
            if count_advertising >= 3:  # Если количество рекламных ссылок больше 3
                until_date = datetime.datetime.now() + datetime.timedelta(hours=int(config.tg_bot.mute_by_bad_word_time))
                try:
                    await bot.restrict_chat_member(chat_id=message.chat.id,
                                                   user_id=message.from_user.id,
                                                   permissions=OnlyReadPermissions,
                                                   until_date=until_date)

                    return await message.answer(f'👤{message.from_user.full_name} '
                                                f'был ограничен в возможности отправлять сообщения '
                                                f'на {config.tg_bot.mute_by_ads_time} часов.\n'
                                                f'📩Причина: Реклама в чате.')
                except:
                    await bot.send_message(chat_id=config.tg_bot.support_id,
                                           text=f'Не удалось заблокироать {message.from_user.id}/{message.from_user.username} по причине рекламы')
            else:
                return await message.answer(f'🔍 Замечена реклама в чате\n'
                                            f'👤 Написал {message.from_user.full_name}\n'
                                            f'🤬 Предупреждение № {count_advertising}\n')
    elif type == 'warn':
        if count_warn > 0:  # Если количество предупреждений больше 0
            if count_warn >= 3:  # Если количество предупреждений больше 3
                until_date = datetime.datetime.now() + datetime.timedelta(hours=int(config.tg_bot.mute_by_bad_word_time))
                try:
                    await bot.restrict_chat_member(chat_id=message.chat.id,
                                                   user_id=message.from_user.id,
                                                   permissions=OnlyReadPermissions,
                                                   until_date=until_date)

                    return await message.answer(f'👤{message.from_user.full_name} '
                                                f'был ограничен в возможности отправлять сообщения '
                                                f'на {config.tg_bot.mute_by_ads_time} часов.\n'
                                                f'📩Причина: предупреждение.')
                except:
                    await bot.send_message(chat_id=config.tg_bot.support_id,
                                           text=f'Не удалось заблокироать {message.from_user.id}/{message.from_user.username} по причине предупреждений')
            else:
                return await message.answer(f'🔍 Вынесено предупреждение\n'
                                            f'👤 Написал {message.from_user.full_name}\n'
                                            f'🤬 Предупреждение № {count_warn}\n')


# Функция обновляет дату последнего поднятия помощи
async def update_last_help_boost(user_id: int):
    logging.info(f'update_last_rep_boost')
    async with async_session() as session:
        chat_user = await session.scalar(select(ChatUser).where(ChatUser.tg_id == user_id))
        chat_user.last_help_boost = datetime.datetime.now()
        await session.commit()


async def info_violations(bot: Bot):
    """
    Действия с нарушениями
    :return:
    """
    logging.info(f'update_last_rep_boost')
    async with async_session() as session:
        violations = await session.scalars(select(ChatUser).order_by(ChatUser.reputation)) # Получаем все нарушения от юзера
    # Получаем каждое нарушение из списка
    text = '<b>Список топ-10 пользователей:</b>\n\n'
    for i, violation in enumerate(violations):
        text += f'{i+1}. @{violation.user_name} - {violation.reputation}\n'
    await bot.send_message(chat_id=config.tg_bot.support_id,
                           text=text)


# Проверяем есть ли юзер написавший сообщение в БД
async def update_group(peer_id: int) -> None:
    logging.info(f'update_group')
    async with async_session() as session:
        group = await session.scalar(select(Group).where(Group.peer_id == peer_id))
        if not group:
            await session.add(Group(**{"id": 1, "peer_id": peer_id}))
            await session.commit()
        else:
            group.peer_id = peer_id
            await session.commit()


"""ORDER"""


@dataclass
class OrderStatus:
    create = "create"
    publish = "publish"
    cancel = "cancel"
    old = "old"
    delete = "delete"
    error = "error"


async def add_order(data: dict) -> None:
    logging.info(f'add_order')
    async with async_session() as session:
        session.add(Order(**data))
        await session.commit()


async def select_order_status(status: str) -> list[Order]:
    logging.info(f'select_order_status')
    async with async_session() as session:
        orders = await session.scalars(select(Order).where(Order.status == status))
        list_order = [order for order in orders]
        return list_order


async def select_order_status_create_tg_id(status: str, create_tg_id: int) -> list[Order]:
    logging.info(f'select_order_status_create_tg_id')
    async with async_session() as session:
        orders = await session.scalars(select(Order).where(Order.status == status, Order.create_tg_id == create_tg_id))
        list_order = [order for order in orders]
        return list_order


async def select_order_id(order_id: int) -> Order:
    logging.info(f'select_order_id')
    async with async_session() as session:
        return await session.scalar(select(Order).where(Order.id == order_id))


async def update_order_status(order_id: int, status: str) -> None:
    logging.info(f'update_order_status')
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == order_id))
        if order:
            order.status = status
            await session.commit()


async def update_order_message(order_id: int, message: str) -> None:
    logging.info(f'update_order_message')
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == order_id))
        if order:
            order.chat_message = message
            await session.commit()


async def update_order_datetime(order_id: int, date_teme: str) -> None:
    logging.info(f'update_order_message')
    async with async_session() as session:
        order = await session.scalar(select(Order).where(Order.id == order_id))
        if order:
            order.time_publish = date_teme
            await session.commit()


"""USER"""


async def add_user(data: dict) -> None:
    logging.info(f'add_user')
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == data['tg_id']))
        if not user:
            session.add(User(**data))
            await session.commit()


async def get_user(tg_id: int) -> User:
    logging.info(f'get_user')
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def get_user_username(username: str) -> User:
    logging.info(f'get_user_username')
    async with async_session() as session:
        return await session.scalar(select(User).where(User.username == username))


"""GROUP"""


async def get_group_topic(type_group: str):
    logging.info(f'get_group_topic')
    async with async_session() as session:
        return await session.scalar(select(Group).where(Group.type_group == type_group))


async def get_groups():
    logging.info(f'get_groups')
    async with async_session() as session:
        return await session.scalars(select(Group))


async def select_chat_actions_top() -> list[ChatUser]:
    logging.info(f'select_chat_action')
    async with async_session() as session:
        chat_users = await session.scalars(select(ChatUser).order_by(desc(ChatUser.reputation)))
        list_chat_users = [user for user in chat_users]
        return list_chat_users