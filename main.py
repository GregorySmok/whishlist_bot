import platform
import asyncio
from config import config
from log_setup import *
from shared import shared
from aiogram import Bot, Dispatcher
from database import db
from aiogram.fsm.storage.memory import MemoryStorage
from middlewares import BanMiddleware
from handlers import routers

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def on_shutdown():
    main_logger.info("Starting bot shutdown...")
    try:
        await shared.bot.session.close()
        main_logger.info("bot session was closed successfully")
        await db.close()
    except Exception as e:
        main_logger.info(f"Error with bot session closig: {e}")

    main_logger.info("Shutdown completed successfully")


async def main():
    main_logger.info("bot starting...")
    token = config.BOT_TOKEN
    shared.bot = Bot(token=token)
    shared.dp = Dispatcher(storage=MemoryStorage())
    shared.dp.message.middleware(BanMiddleware())
    try:
        main_logger.info("Including routers...")
        for router in routers:
            shared.dp.include_router(router)
        main_logger.info("Succesfull")
        main_logger.info("Polling starting...")
        await shared.dp.start_polling(shared.bot)
    except Exception as e:
        main_logger.error(f"Critical error: {e}")
        raise
    finally:
        await on_shutdown()
        main_logger.info("bot is stopped")


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        main_logger.info("Exit is caught...")
    except Exception as e:
        main_logger.error(f"Uncaught error: {e}")
    finally:
        try:
            tasks = asyncio.all_tasks(loop)
            for task in tasks:
                task.cancel()
            if tasks:
                loop.run_until_complete(asyncio.gather(
                    *tasks, return_exceptions=True))
            loop.close()
        except Exception as e:
            main_logger.error(f"Error with loop closing: {e}")
        main_logger.info("Program is finished")
