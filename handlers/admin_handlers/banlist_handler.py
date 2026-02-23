from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.types import Message

from database import db
from log_setup import log_admin_action
from shared import shared
from states import States


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["banlist"]))
    async def get_banlist(message: Message):
        users = [i[0] for i in await db.fetch_all("SELECT username FROM banlist")]
        text = "Заблокированные пользователи:\n"
        for num, user in enumerate(users):
            text += f"{num + 1}. @{user}\n"
        await shared.bot.send_message(message.chat.id, text)

        # Логирование действия администратора
        log_admin_action(
            admin_id=message.chat.id,
            admin_username=message.from_user.username or str(message.chat.id),
            action="view_banlist",
            details=f"Просмотр списка заблокированных пользователей (всего: {len(users)})",
        )
