import asyncio
import platform
from typing import List

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database import db
from handlers import routers
from log_setup import *
from middlewares import BanMiddleware
from shared import shared

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def on_shutdown() -> None:
    """Корректно завершает работу бота и закрывает соединения."""
    main_logger.info("Starting bot shutdown...")
    try:
        await shared.bot.session.close()
        main_logger.info("Bot session was closed successfully")
        await db.close()
        main_logger.info("Database connection closed successfully")
    except Exception as e:
        main_logger.error(f"Error with bot session closing: {e}")

    main_logger.info("Shutdown completed successfully")


async def setup_routers(dp: Dispatcher, router_list: List[Router]) -> None:
    """Подключает все роутеры к диспетчеру."""
    main_logger.info("Including routers...")
    for router in router_list:
        dp.include_router(router)
    main_logger.info("Routers included successfully")


async def main() -> None:
    """Основная функция запуска бота."""
    main_logger.info("Bot starting...")
    token = config.BOT_TOKEN
    shared.bot = Bot(token=token)
    shared.dp = Dispatcher(storage=MemoryStorage())
    shared.dp.message.middleware(BanMiddleware())

    try:
        await setup_routers(shared.dp, routers)
        main_logger.info("Polling starting...")
        await shared.dp.start_polling(shared.bot)
    except Exception as e:
        main_logger.error(f"Critical error: {e}")
        raise
    finally:
        await on_shutdown()
        main_logger.info("Bot is stopped")


async def cleanup_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Отменяет все задачи в цикле событий."""
    tasks = asyncio.all_tasks(loop)
    if not tasks:
        return

    main_logger.info(f"Cancelling {len(tasks)} outstanding tasks...")

    # Исключаем текущую задачу из списка отменяемых задач
    current_task = asyncio.current_task(loop)
    tasks_to_cancel = [t for t in tasks if t is not current_task and not t.done()]

    # Отменяем задачи без рекурсивных вызовов
    for task in tasks_to_cancel:
        task.cancel()

    if tasks_to_cancel:
        try:
            # Устанавливаем таймаут для ожидания отмены задач
            await asyncio.wait(tasks_to_cancel, timeout=5.0)
            main_logger.info("All tasks have been cancelled")
        except Exception as e:
            main_logger.error(f"Error while waiting for tasks to cancel: {e}")

    # Не закрываем цикл событий здесь, это будет сделано в основном блоке


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt detected, shutting down...")
    except Exception as e:
        main_logger.error(f"Uncaught error: {e}")
    finally:
        try:
            # Отменяем задачи
            loop.run_until_complete(cleanup_tasks(loop))

            # Останавливаем цикл событий
            loop.run_until_complete(loop.shutdown_asyncgens())
            if hasattr(loop, "shutdown_default_executor"):
                loop.run_until_complete(loop.shutdown_default_executor())

            # Закрываем цикл событий только после завершения всех задач
            if not loop.is_closed():
                loop.close()
                main_logger.info("Event loop closed")
        except Exception as e:
            main_logger.error(f"Error during cleanup: {e}")
        main_logger.info("Program finished successfully")
