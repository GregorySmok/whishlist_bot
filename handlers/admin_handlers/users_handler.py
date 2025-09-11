from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared
from log_setup import log_admin_action


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["users"]))
    async def get_users(message: Message):
        users = list(await db.fetch_all("SELECT username, list_id FROM users"))
        users.sort(key=lambda x: (x[0]))
        text = "Пользователи:\n"
        for num, user in enumerate(users):
            if user[1]:
                text += f"{num + 1}. @{user[0]} (активен)\n"
            else:
                text += f"{num + 1}. @{user[0]} (не активен)\n"
        await shared.bot.send_message(message.chat.id, text)

        # Логирование действия администратора
        log_admin_action(
            admin_id=message.chat.id,
            admin_username=message.from_user.username or str(message.chat.id),
            action="view_users",
            details=f"Просмотр списка пользователей (всего: {len(users)})",
        )
