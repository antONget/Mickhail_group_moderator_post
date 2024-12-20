from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def keyboard_process_order(count_create: int, count_publish: int, count_cancel: int) -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text=f"Заявки на размещение ({count_create})", callback_data='order_create')
    button_2 = InlineKeyboardButton(text=f"Опубликованные ({count_publish})", callback_data='order_publish')
    # button_3 = InlineKeyboardButton(text=f"Отклоненные ({count_cancel})", callback_data='order_cancel')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_publish(id_order: int) -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text=f"Опубликовать заявку", callback_data=f'publish_{id_order}')
    button_2 = InlineKeyboardButton(text=f"Отменить публикацию", callback_data=f'cancel_{id_order}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_delete(id_order: int) -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text=f"Удалить объявление", callback_data=f'delete_{id_order}')
    button_2 = InlineKeyboardButton(text=f"<<", callback_data=f'pubback_{id_order}')
    button_3 = InlineKeyboardButton(text=f">>", callback_data=f'pubforward_{id_order}')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard
