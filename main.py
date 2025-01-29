import asyncio

from aiogram import F
from aiogram import Bot, Dispatcher, types, BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Dict, Any, Callable, Awaitable
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import platform

token = "7802068134:AAFrKpQwLbpTOCsurdGw0QfBPVvOd6oR8_g"
bot = Bot(token=token)
dp = Dispatcher()


class States(StatesGroup):
    already_started = State()


if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@dp.message(
    StateFilter(default_state, States.already_started), Command(
        commands=["start"])
)
async def start_handler(message: Message, state: FSMContext):


async def on_shutdown():
    print("Начало завершения работы бота...")
    try:
        await bot.session.close()
        print("Сессия бота закрыта")
    except Exception as e:
        print(f"Ошибка при закрытии сессии бота: {e}")

    print("Shutdown завершен")


async def main():
    print("Запуск бота...")

    try:
        # Запускаем startup
        # await on_startup()

        # Запускаем поллинг
        print("Запуск поллинга...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        raise
    finally:
        # Выполняем shutdown в любом случае
        await on_shutdown()
        print("Бот остановлен")


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Запускаем main() и ждем его завершения
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Получено прерывание...")
    except Exception as e:
        print(f"Необработанная ошибка: {e}")
    finally:
        # Закрываем loop
        try:
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                task.cancel()

            # Ждем завершения всех задач
            if tasks:
                loop.run_until_complete(asyncio.gather(
                    *tasks, return_exceptions=True))

            loop.close()
        except Exception as e:
            print(f"Ошибка при закрытии loop: {e}")

        print("Программа завершена")
