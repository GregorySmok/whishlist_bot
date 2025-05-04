from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["banlist"]))
    async def get_banlist(message: Message):
        users = [i[0] for i in await db.fetch_all("SELECT username FROM banlist")]
        text = "Заблокированные пользователи:\n"
        for num, user in enumerate(users):
            text += f"{num + 1}. @{user}\n"
        await shared.bot.send_message(message.chat.id, text)
