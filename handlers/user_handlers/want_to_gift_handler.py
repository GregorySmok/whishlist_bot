from aiogram.types import CallbackQuery
from shared import shared
from log_setup import log_error
import traceback
from aiogram import F
from keyboards.inline import update_present_button


def setup(router):
    @router.callback_query(F.data.startswith("want^"))
    async def want_to_gift(callback_query: CallbackQuery):
        try:
            friend_name, gift_id, action = callback_query.data.split("^")[1::]
            new_markup = await update_present_button(
                callback_query, action, friend_name, gift_id)
            await callback_query.message.edit_reply_markup(reply_markup=new_markup.as_markup())
            await callback_query.answer()
        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error in want_to_gift: {e}",
                error_traceback,
            )
            await callback_query.answer("Произошла ошибка")
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Произошла ошибка при изменении статуса дарения. Пожалуйста, попробуйте позже.",
            )
