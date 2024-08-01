from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_keyboard() -> ReplyKeyboardMarkup:
    # Создаем кнопки
    start_button = KeyboardButton('Начать отслеживание сообщений')
    stop_button = KeyboardButton('Прекратить отслеживание сообщений')
    summarize_button = KeyboardButton('Перескажи кратко чат')
    create_note_button = KeyboardButton('Создать заметку')
    delete_note_button = KeyboardButton('Удалить заметку')

    # Создаем клавиатуру и добавляем кнопки
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(start_button, stop_button)
    keyboard.add(summarize_button)
    keyboard.add(create_note_button, delete_note_button)

    return keyboard