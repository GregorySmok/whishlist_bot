from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from shared import shared
from log_setup import log_user_action, log_error
import traceback
from keyboards.reply import set_default_keyboard
from utils import show_friends_page


def setup(router):
    @router.message(StateFilter(States.already_started), Command(commands=["друзья"]))
    async def cmd_friends(message: Message):
        try:
            # Отправляем первую страницу
            await show_friends_page(message, user_id=message.from_user.id, page=0)
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "view_friends_list",
                "User viewed friends list",
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(message.from_user.id,
                      f"Error in cmd_friends: {e}", error_traceback)
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при загрузке списка друзей. Пожалуйста, попробуйте позже.",
            )
            await set_default_keyboard(message.from_user.id)
