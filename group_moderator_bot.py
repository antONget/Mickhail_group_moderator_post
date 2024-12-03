import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile, User
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

import traceback
from typing import Any, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config_data.config import Config, load_config
from database.requests import info_violations
from handlers import other_handlers, user_handlers, manager_handlers, post_attach
from handlers.group import group_link_and_bad_word, group_mute, group_info, group_rep, service_messages, group_kick_, \
    group_ban, group_unban, group_warn
from notify_admins import on_startup_notify
from middleware.throttling import ThrottlingMiddleware
from database.models import async_main
# Инициализируем logger
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main():
    await async_main()
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        # filename="py_log.log",
        # filemode='w',
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    # scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    # scheduler.add_job(info_violations, 'cron', minute="*", args=(bot,))
    # scheduler.start()
    await on_startup_notify(bot=bot)
    # Регистрируем router в диспетчере
    dp.include_router(service_messages.router)
    dp.include_routers(group_mute.router, group_info.router, group_rep.router, group_kick_.router, group_ban.router,
                       group_unban.router, group_warn.router, group_link_and_bad_word.router)
    dp.include_router(user_handlers.router)
    dp.include_router(manager_handlers.router)
    dp.include_router(post_attach.router)
    dp.include_router(other_handlers.router)

    # dp.callback_query.middleware(ThrottlingMiddleware())
    # dp.message.middleware(ThrottlingMiddleware())

    @dp.error()
    async def error_handler(event: ErrorEvent, data: Dict[str, Any]):
        logger.critical("Критическая ошибка: %s", event.exception, exc_info=True)
        user: User = data.get('event_from_user')
        await bot.send_message(chat_id=user.id,
                               text='Упс.. Что-то пошло не так( Перезапустите бота /start')
        await bot.send_message(chat_id=config.tg_bot.support_id,
                               text=f'{event.exception}')
        formatted_lines = traceback.format_exc()
        text_file = open('error.txt', 'w')
        text_file.write(str(formatted_lines))
        text_file.close()
        await bot.send_document(chat_id=config.tg_bot.support_id,
                                document=FSInputFile('error.txt'))

    # Пропускаем накопившиеся update и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
