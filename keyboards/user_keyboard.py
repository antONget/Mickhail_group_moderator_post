from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def keyboard_main_button() -> ReplyKeyboardMarkup:
    button_1 = KeyboardButton(text='Частное объявление')
    button_2 = KeyboardButton(text='Коммерческое объявление')
    button_3 = KeyboardButton(text='Услуги')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2], [button_3]],
                                   resize_keyboard=True)
    return keyboard


def keyboard_main_manager() -> ReplyKeyboardMarkup:
    button_1 = KeyboardButton(text='Частное объявление')
    button_2 = KeyboardButton(text='Коммерческое объявление')
    button_3 = KeyboardButton(text='Услуги')
    button_4 = KeyboardButton(text='Заявки')
    keyboard = ReplyKeyboardMarkup(keyboard=[[button_1], [button_2], [button_3], [button_4]],
                                   resize_keyboard=True)
    return keyboard


def keyboard_continue() -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text='Продолжить', callback_data='continue')
    button_2 = InlineKeyboardButton(text='Добавить еще', callback_data='add_photo')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard


def keyboard_services() -> InlineKeyboardMarkup:
    button_1 = InlineKeyboardButton(text='Платное размещение', callback_data='paid')
    button_2 = InlineKeyboardButton(text='Бесплатное размещение', callback_data='free_charge')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]])
    return keyboard



