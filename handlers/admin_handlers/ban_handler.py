from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["ban"]))
    async def ban_handler(message: Message):
        user = message.text.split()[1]
        try:
            await db.execute("INSERT INTO banlist (username) VALUES (%s)", (user,))
            await shared.bot.send_message(
                message.chat.id, f"Пользователь @{user} успешно заблокирован.")
        except:
            await shared.bot.send_message("Не удалось заблокировать этого пользователя")
