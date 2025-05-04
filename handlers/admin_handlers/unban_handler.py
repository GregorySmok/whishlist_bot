from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["unban"]))
    async def unban_handler(message: Message):
        user = message.text.split()[1]
        try:
            await db.execute("DELETE FROM banlist WHERE username = %s", (user,))
            await shared.bot.send_message(
                message.chat.id, f"Пользователь @{user} успешно разблокирован")
        except:
            await shared.bot.send_message("Не удалось разблокировать этого пользователя")
