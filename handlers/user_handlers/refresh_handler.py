from aiogram.types import Message
from shared import shared
from aiogram.fsm.state import default_state


def setup(router):
    @router.message(default_state)
    async def refresh_handler(message: Message):
        await shared.bot.send_message(message.from_user.id, "Сервер был перезагружен. Нажмите /start")
