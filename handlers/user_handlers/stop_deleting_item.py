from states import States
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.filters.state import StateFilter
from shared import shared
from aiogram.fsm.context import FSMContext
from log_setup import log_user_action, log_error
import traceback
from keyboards.reply import set_default_keyboard


def setup(router):
    @router.callback_query(F.data == "stop_deleting", StateFilter(States.deleting_item))
    async def stop_deleting(callback_query: CallbackQuery, state: FSMContext):
        try:
            await callback_query.answer()
            await callback_query.message.delete()
            await shared.bot.send_message(
                callback_query.from_user.id, "Удаление товаров остановлено."
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(callback_query.from_user.id)
            log_user_action(
                callback_query.from_user.id,
                callback_query.from_user.username,
                "delete_item_stopped",
                "User finished deleting items",
            )
        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id, f"Error in stop_deleting: {e}", error_traceback
            )
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Произошла ошибка. Пожалуйста, попробуйте позже.",
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(callback_query.from_user.id)
