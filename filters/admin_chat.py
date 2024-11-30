from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import BaseFilter
from aiogram.enums.chat_member_status import ChatMemberStatus
from config_data.config import load_config, Config

config: Config = load_config()


# настраиваемый фильтр для приватного чата с ботом (для Администраторов)
# Проверка айди в data.config и в БД
async def check_admin_project(message: Message) -> bool:
    print(message.chat.id)
    if message.from_user.id in config.tg_bot.admin_ids.split(','):
        return True
    else:
        await message.answer('⛔️Вы не Администратор! Данная команда не доступна⛔️')


class IsAdminCheck(BaseFilter):
    """
    Фильтр на администратора проекта
    """
    async def __call__(self, message: Message) -> bool | None:
        return await check_admin_project(message=message)


async def check_admin_chat(message: Message, bot: Bot) -> bool:
    chat_member = await bot.get_chat_member(chat_id=message.chat.id, user_id=message.from_user.id)
    admin_types = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    return chat_member.status in admin_types


class IsAdminChat(BaseFilter):
    """
    Фильтр на администратора или создателя чата
    """
    async def __call__(self, message: Message, bot: Bot) -> bool:
        return await check_admin_chat(message=message, bot=bot)
