from states import States
from aiogram.types import CallbackQuery
from aiogram.filters.state import StateFilter
from database import db
from shared import shared
from log_setup import log_user_action, log_error
import traceback
from aiogram import F


def setup(router):
    @router.callback_query(
        F.data.startswith("accept_friend"), StateFilter(States.already_started)
    )
    async def accept_friend(callback_query: CallbackQuery):
        try:
            friend_id = callback_query.data.split("^")[1]
            user_id = callback_query.from_user.id
            friend_name = (
                await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend_id,))
            )[0]

            await callback_query.answer()

            # Обновление статуса дружбы
            await db.execute(
                "UPDATE friends_list SET status = 'accepted' WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
                (user_id, friend_id, user_id, friend_id),
            )

            # Отправка уведомлений
            await shared.bot.send_message(
                int(friend_id),
                f"@{callback_query.from_user.username} принял ваш запрос дружбы.",
            )
            await shared.bot.send_message(int(user_id), f"Вы добавили @{friend_name} в друзья.")

            log_user_action(
                user_id,
                callback_query.from_user.username,
                "accept friend" f"accepted friend request from @{friend_name}",
            )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(user_id, f"Error in accept_friend: {e}", error_traceback)
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Произошла ошибка при принятии запроса дружбы. Попробуйте позже.",
            )
