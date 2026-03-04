import traceback

from aiogram import F
from aiogram.types import CallbackQuery

from keyboards.inline import update_present_button
from log_setup import log_error


def setup(router):
    @router.callback_query(F.data.startswith("want^"))
    async def want_to_gift(callback_query: CallbackQuery):
        try:
            _, friend_id, gift_id, action = callback_query.data.split("^")
            new_markup = await update_present_button(
                callback_query, action, int(friend_id), int(gift_id)
            )
            await callback_query.message.edit_reply_markup(
                reply_markup=new_markup.as_markup()
            )
            await callback_query.answer()
        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error in want_to_gift: {e}",
                error_traceback,
            )
            await callback_query.answer("Произошла ошибка")
