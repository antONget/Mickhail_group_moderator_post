import re
import logging


def validate_russian_phone_number(phone_number: str) -> bool:
    """
    Валидация номера телефона
    :param phone_number:
    :return:
    """
    logging.info('validate_russian_phone_number')
    # Паттерн для российских номеров телефона
    # Российские номера могут начинаться с +7, 8, или без кода страны
    pattern = re.compile(r'^(\+7|8|7)?(\d{10})$')
    # Проверка соответствия паттерну
    match = pattern.match(phone_number)
    return bool(match)


def validate_date_format(date: str, split: str) -> bool | list:
    """
    Валидация на формат даты дд-мм-гггг
    :param date:
    :param split:
    :return:
    """
    logging.info('validate_date_birthday')
    # Паттерн для даты рождения дд-мм-гггг
    if split == '-':
        pattern = re.compile(r'\b(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-([0-9]{4})\b')
        match = pattern.match(date)
        if bool(match):
            return date.split('-')
        else:
            return False
    elif split == '.':
        pattern = re.compile(r'\b(0[1-9]|[12][0-9]|3[01]).(0[1-9]|1[0-2]).([0-9]{4})\b')
        match = pattern.match(date)
        if bool(match):
            return date.split('.')
        else:
            return False


def validate_email(email: str):
    """
    Валидация на формат электронной почты
    :param email:
    :return:
    """
    logging.info('validate_email')
    pattern = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    # Проверка соответствия паттерну
    match = pattern.match(email)
    return bool(match)


def validate_text_latin(text: str):
    """
    Валидация на строку на наличие только латинских букв и цифр
    :param text:
    :return:
    """
    logging.info('validate_text_latin')
    pattern = re.compile(r'^[A-Za-z0-9 ]*$')
    # Проверка соответствия паттерну
    match = pattern.match(text)
    return bool(match)


if __name__ == "__main__":
    print(validate_text_latin('Ford Focus'))