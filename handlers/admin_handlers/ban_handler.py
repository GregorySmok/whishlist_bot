from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.types import Message

from database import db
from log_setup import log_admin_action
from shared import shared
from states import States


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["ban"]))
    async def ban_handler(message: Message):
        user = message.text.split()[1]
        try:
            await db.execute("INSERT INTO banlist (username) VALUES (%s)", (user,))
            await shared.bot.send_message(
                message.chat.id, f"Пользователь @{user} успешно заблокирован."
            )

            # Логирование действия администратора
            log_admin_action(
                admin_id=message.chat.id,
                admin_username=message.from_user.username or str(message.chat.id),
                action="ban_user",
                target=user,
                details=f"Блокировка пользователя @{user}",
            )
        except Exception as e:
            await shared.bot.send_message(
                message.chat.id, "Не удалось заблокировать этого пользователя"
            )

            # Логирование ошибки
            log_admin_action(
                admin_id=message.chat.id,
                admin_username=message.from_user.username or str(message.chat.id),
                action="ban_user_failed",
                target=user,
                details=f"Ошибка при блокировке пользователя @{user}: {str(e)}",
            )
