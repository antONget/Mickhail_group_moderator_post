from database import requests as rq
from config_data.config import words_of_gratitude
from aiogram.types import Message
import logging


async def word_of_gradit(message: Message, text_: list):
    logging.info(f'word_of_gradit {message.from_user.id}')
    text_str = ''.join(text_)
    for word_of_gratitude in words_of_gratitude:
        if word_of_gratitude.lower().replace(' ', '') in text_str:
            print(f'{message.reply_to_message}')
            print(f'{bool(message.reply_to_message.text)} {bool(message.reply_to_message.photo)} {bool(message.reply_to_message.document)}')
            if not message.reply_to_message.text and not message.reply_to_message.photo and not bool(message.reply_to_message.document):
                await message.answer(
                    'Для того чтобы благодарность зачлась пользователю нужно ответить на его сообщение')
                return
            elif message.reply_to_message.from_user.id == message.from_user.id:
                await message.answer('👮‍♂ Даже не пытайся накрутить себе хорошую статистику')
                return
            else:
                user_plus = message.reply_to_message.from_user.id
            if message.reply_to_message:
                chat_user = await rq.select_chat_user(message.from_user.id)
                if chat_user:
                    # if chat_user.last_help_boost <= datetime.datetime.now() - datetime.timedelta(hours=float(config.tg_bot.time_of_help)):
                    helping_user = await rq.select_chat_user(user_plus)
                    chat_user = await rq.select_chat_user(message.from_user.id)
                    await rq.add_total_help(helping_user.tg_id)
                    await rq.add_reputation(user_id=helping_user.tg_id)
                    await rq.add_chat_action(user_id=message.from_user.id,
                                             type_='help boost')
                    await rq.update_last_help_boost(message.from_user.id)
                    await message.reply(f'👤 {message.reply_to_message.from_user.full_name}'
                                        f' ({helping_user.total_help} помощи)\n'
                                        f'помог {message.from_user.full_name} ({chat_user.total_help}'
                                        f' помощи) и получает +1 в свой рейтинг.')
                    # else:
                    #     await message.reply(f'🚫 Вы не можете сказать сказать слова благодарности'
                    #                         f' ещё {str(datetime.datetime.now() + datetime.timedelta(hours=float(config.tg_bot.time_of_help)) - chat_user.last_help_boost).split(".")[0]}')