from aiogram import Bot
from config_data.config import Config, load_config

config: Config = load_config()


async def send_message_admins(bot: Bot, text: str):
    """
    Рассылка сообщения администраторам
    :param bot:
    :param text:
    :return:
    """
    list_admins = config.tg_bot.admin_ids.split(',')
    for admin in list_admins:
        try:
            await bot.send_message(chat_id=admin,
                                   text=text)
        except:
            pass


async def send_message_manager(bot: Bot, text: str):
    """
    Рассылка сообщения менеджерам
    :param bot:
    :param text:
    :return:
    """
    list_manager = config.tg_bot.manager_ids.split(',')
    for manager in list_manager:
        try:
            await bot.send_message(chat_id=manager,
                                   text=text)
        except:
            pass