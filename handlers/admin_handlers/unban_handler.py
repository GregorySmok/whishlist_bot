from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared
from log_setup import log_admin_action


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["unban"]))
    async def unban_handler(message: Message):
        user = message.text.split()[1]
        try:
            await db.execute("DELETE FROM banlist WHERE username = %s", (user,))
            await shared.bot.send_message(
                message.chat.id, f"Пользователь @{user} успешно разблокирован")
            
            # Логирование действия администратора
            log_admin_action(
                admin_id=message.chat.id,
                admin_username=message.from_user.username or str(message.chat.id),
                action="unban_user",
                target=user,
                details=f"Разблокировка пользователя @{user}"
            )
        except Exception as e:
            await shared.bot.send_message(message.chat.id, "Не удалось разблокировать этого пользователя")
            
            # Логирование ошибки
            log_admin_action(
                admin_id=message.chat.id,
                admin_username=message.from_user.username or str(message.chat.id),
                action="unban_user_failed",
                target=user,
                details=f"Ошибка при разблокировке пользователя @{user}: {str(e)}"
            )