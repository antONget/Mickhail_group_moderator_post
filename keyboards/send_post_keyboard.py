from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def keyboard_continue() -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text='Пропустить', callback_data='pass_add_content')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]])
    return keyboard


def keyboard_method() -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text='OBD2', callback_data='method_OBD2')
    button_2 = InlineKeyboardButton(text='Разбор блока', callback_data='method_Разбор блока')
    button_3 = InlineKeyboardButton(text='Пропустить', callback_data='pass_add_content')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2], [button_3]])
    return keyboard


def keyboard_ebu() -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text='DASHBOARD', callback_data='ebu_DASHBOARD')
    button_2 = InlineKeyboardButton(text='SRS', callback_data='ebu_SRS')
    button_3 = InlineKeyboardButton(text='ECM', callback_data='ebu_ECM')
    button_4 = InlineKeyboardButton(text='ВCM', callback_data='ebu_ВCM')
    button_5 = InlineKeyboardButton(text='IMMO', callback_data='ebu_IMMO')
    button_6 = InlineKeyboardButton(text='MUSIK', callback_data='ebu_MUSIK')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3], [button_4], [button_5],
                                                     [button_6]])
    return keyboard


def keyboard_photo() -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text='Опубликовать', callback_data='post_publish')
    button_2 = InlineKeyboardButton(text='Добавить фото', callback_data='add_photo_post')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard
