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
        try:
            friend_id = int(callback_query.data.split("_")[1])
            friend_name, friend_list = await db.fetch_one(
                "SELECT username, list_id FROM users WHERE id = %s",
                (friend_id,),
            )
            my_list = (
                await db.fetch_one(
                    "SELECT list_id FROM users WHERE id = %s",
                    (callback_query.from_user.id,),
                )
            )[0]

            wishes = [
                i
                for i in await db.fetch_all(f"SELECT id, stuff_link FROM {friend_list}")
            ]

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
                await callback_query.answer()
                return

            await shared.bot.send_message(
                callback_query.from_user.id, f"Вишлист @{friend_name}:"
            )
            for id_, link in wishes:
                builder = await want_to_present_button(my_list, friend_list, id_)

                await shared.bot.send_message(
                    callback_query.from_user.id, link, reply_markup=builder.as_markup()
                )

            log_user_action(
                callback_query.from_user.id,
                callback_query.from_user.username,
                "view_friend_wishlist",
                f"User viewed wishlist of friend @{friend_name} with {len(wishes)} items",
            )
            # Подтверждаем обработку callback
            await callback_query.answer()

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error in process_friend_selection: {e}",
                error_traceback,
            )
            await callback_query.answer("Произошла ошибка")
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Произошла ошибка при загрузке вишлиста друга. Пожалуйста, попробуйте позже или попросите пользователя запустить бота командой /start.",
            )
