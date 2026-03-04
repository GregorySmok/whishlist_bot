import traceback

from aiogram import F
from aiogram.filters.state import StateFilter
from aiogram.types import CallbackQuery

from database import db
from log_setup import log_error, log_user_action
from shared import shared
from states import States


def setup(router):
    @router.callback_query(F.data.startswith("del_"), StateFilter(States.deleting_item))
    async def delete_item(callback_query: CallbackQuery):
        await callback_query.answer()  # Гасим часики загрузки!
        try:
            item_id = int(callback_query.data.replace("del_", ""))
            username = callback_query.from_user.username
            user_id = callback_query.from_user.id

            item_exists = await db.fetch_one(
                "SELECT stuff_link FROM wishlist_items WHERE id = %s AND user_id = %s",
                (item_id, user_id),
            )

            if item_exists:
                deleted_link = item_exists[0]
                await db.execute("DELETE FROM wishlist_items WHERE id = %s", (item_id,))
                await db.execute(
                    "DELETE FROM want_to_present WHERE gift = %s", (item_id,)
                )

                await callback_query.message.delete()
                log_user_action(
                    user_id,
                    username,
                    "delete_item_success",
                    f"Deleted item: {deleted_link}",
                )
            else:
                log_user_action(
                    user_id,
                    username,
                    "delete_item_not_found",
                    f"Item ID not found: {item_id}",
                )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error while deleting item: {e}",
                error_traceback,
            )
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Не удалось удалить товар. Пожалуйста, попробуйте позже.",
            )
