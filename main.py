from aiogram import executor
from db import dp

# Импортируем обработчики
import handlers

if __name__ == "__main__":
    # Регистрируем обработчики
    handlers.register_handlers(dp)

    # Запускаем бота
    executor.start_polling(dp, skip_updates=True)