from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared
from log_setup import log_error, log_admin_action
import traceback


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["notification"]))
    async def notify_handler(message: Message):
        text = " ".join(message.text.split()[1:])
        users = [i[0] for i in await db.fetch_all("SELECT id FROM users")]
        
        # Логирование начала рассылки
        log_admin_action(
            admin_id=message.chat.id,
            admin_username=message.from_user.username or str(message.chat.id),
            action="notification_start",
            details=f"Начало рассылки уведомления для {len(users)} пользователей"
        )
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                await shared.bot.send_message(user, text)  # Исправлена опечатка botbot -> bot
                success_count += 1
            except Exception as e:
                error_count += 1
                log_error(
                    message.from_user.id,
                    f"Error sending notification: {e}",
                    traceback.format_exc(),
                )
        
        # Логирование завершения рассылки
        log_admin_action(
            admin_id=message.chat.id,
            admin_username=message.from_user.username or str(message.chat.id),
            action="notification_complete",
            details=f"Завершение рассылки: успешно {success_count}, ошибок {error_count}"
        )
        
        # Отправка отчета администратору
        await shared.bot.send_message(
            message.chat.id, 
            f"Рассылка завершена: успешно отправлено {success_count} из {len(users)} сообщений."
        )