from aiogram.types import Message
from aiogram.enums.chat_type import ChatType
from aiogram.filters import BaseFilter


async def check_groups(message: Message):
    group_types = [ChatType.GROUP, ChatType.SUPERGROUP]
    return message.chat.type in group_types


class IsGroup(BaseFilter):
    async def __call__(self, message: Message) -> bool | None:
        return await check_groups(message=message)
