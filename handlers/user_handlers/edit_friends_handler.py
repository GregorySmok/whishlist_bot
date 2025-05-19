from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from shared import shared
from log_setup import log_user_action, log_error
import traceback
from database import db
from keyboards.reply import set_default_keyboard, set_edit_friends_button
from utils import show_friends_page


def setup(router):
    @router.message(StateFilter(States.already_started), Command(commands=["редактировать"]))
    async def edit_friends_handler(message: Message, state: FSMContext):
        friends = [
            i[0] if i[1] == message.from_user.id else i[1]
            for i in await db.fetch_all(
                "SELECT user_1, user_2 FROM friends_list WHERE (user_1 = %s OR user_2 = %s) AND status = 'accepted'",
                (message.from_user.id, message.from_user.id),
            )
        ]
        if len(friends) == 0:
            await message.answer("Вы пока не добавили ни одного друга")
            return
        for friend in friends:
            await shared.bot.send_message(
                message.from_user.id,
                str(friend)
            )
