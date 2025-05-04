from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared
from log_setup.logging_setup import log_error
import traceback


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["notification"]))
    async def notify_handler(message: Message):
        text = " ".join(message.text.split()[1:])
        users = [i[0] for i in await db.fetch_all("SELECT id FROM users")]
        for user in users:
            try:
                await shared.botbot.send_message(user, text)
            except Exception as e:
                log_error(
                    message.from_user.id,
                    f"Error sending notification: {e}",
                    traceback.format_exc(),
                )
