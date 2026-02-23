import traceback

from aiogram import F
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from emoji import emojize

from keyboards.reply import set_default_keyboard
from log_setup import log_error, log_user_action
from shared import shared
from states import States


def setup(router):
    @router.message(
        StateFilter(States.already_started),
        F.text == emojize(":wrapped_gift: Добавить"),
    )
    async def add_item_handler(message: Message, state: FSMContext):
        try:
            await state.set_state(States.adding_item)
            await shared.bot.send_message(
                message.from_user.id,
                "Отправьте сюда ссылку на товар без лишних символов или введите 0 для выхода:",
            )
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "add_item_started",
                "User initiated adding item",
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                message.from_user.id, f"Error in add_item_handler: {e}", error_traceback
            )
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при попытке добавить товар. Пожалуйста, попробуйте позже.",
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
