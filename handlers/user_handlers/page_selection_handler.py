import traceback

from aiogram import F
from aiogram.types import CallbackQuery

from log_setup import log_error, log_user_action
from shared import shared
from utils import show_friends_page


def setup(router):
    @router.callback_query(F.data.startswith("page_"))
    async def process_page_selection(callback_query: CallbackQuery):
        try:
            page = int(callback_query.data.split("_")[1])
            await show_friends_page(
                callback_query.message, user_id=callback_query.from_user.id, page=page
            )
            await callback_query.answer()
            log_user_action(
                callback_query.from_user.id,
                callback_query.from_user.username,
                "navigate_friends_page",
                f"User navigated to friends page {page + 1}",
            )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error in process_page_selection: {e}",
                error_traceback,
            )
            await callback_query.answer("Произошла ошибка при навигации")
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Произошла ошибка при переходе на другую страницу. Пожалуйста, попробуйте позже.",
            )
