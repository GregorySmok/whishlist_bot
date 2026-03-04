import traceback

from aiogram import F
from aiogram.types import CallbackQuery

from database import db
from keyboards.inline import want_to_present_button
from keyboards.reply import set_default_keyboard
from log_setup import log_error, log_user_action
from shared import shared


def setup(router):
    @router.callback_query(F.data.startswith("friend_"))
    async def process_friend_selection(callback_query: CallbackQuery):
        await callback_query.answer()
        try:
            friend_id = int(callback_query.data.split("_")[1])
            friend_name = (
                await db.fetch_one(
                    "SELECT username FROM users WHERE id = %s", (friend_id,)
                )
            )[0]
            my_id = callback_query.from_user.id

            wishes = await db.fetch_all(
                "SELECT id, stuff_link FROM wishlist_items WHERE user_id = %s",
                (friend_id,),
            )

            if not wishes:
                await shared.bot.send_message(
                    callback_query.from_user.id, f"Вишлист @{friend_name} пуст."
                )
                await set_default_keyboard(callback_query.from_user.id)
                log_user_action(
                    callback_query.from_user.id,
                    callback_query.from_user.username,
                    "view_friend_empty_wishlist",
                    f"User viewed empty wishlist of friend @{friend_name}",
                )
                return

            await shared.bot.send_message(
                callback_query.from_user.id, f"Вишлист @{friend_name}:"
            )
            for item_id, link in wishes:
                # Передаем напрямую ID пользователей, а не названия таблиц
                builder = await want_to_present_button(my_id, friend_id, item_id)
                await shared.bot.send_message(
                    callback_query.from_user.id, link, reply_markup=builder.as_markup()
                )

            log_user_action(
                callback_query.from_user.id,
                callback_query.from_user.username,
                "view_friend_wishlist",
                f"User viewed wishlist of friend @{friend_name} with {len(wishes)} items",
            )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error in process_friend_selection: {e}",
                error_traceback,
            )
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Произошла ошибка при загрузке вишлиста друга.",
            )
