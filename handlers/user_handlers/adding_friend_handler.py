from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from database import db
from shared import shared
from aiogram.fsm.context import FSMContext
from log_setup import log_user_action, log_error, main_logger
import traceback
from keyboards.reply import set_default_keyboard
from aiogram import F
from datetime import datetime
from keyboards.inline import accept_request_kb


def setup(router):
    @router.message(StateFilter(States.already_started), F.user_shared)
    async def adding_friend(message: Message, state: FSMContext):
        try:
            friend_id = message.user_shared.user_id
            users_list = [i[0] for i in await db.fetch_all("SELECT id FROM users")]

            if friend_id not in users_list:
                await shared.bot.send_message(
                    message.chat.id, f"Пользователь не зарегистрирован в данном боте."
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "invalid_input",
                    f"tried to add non-existent user: {friend_id}",
                )
                return

            if friend_id == message.from_user.id:
                await shared.bot.send_message(
                    message.chat.id, "Вы не можете добавить себя в друзья."
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "invalid_input",
                    "tried to add themselves as friend",
                )
                return

            user1 = message.from_user.id
            user2 = friend_id
            username = (await shared.bot.get_chat(friend_id)).username
            # Проверяем историю запросов дружбы
            old_request = await db.fetch_one(
                "SELECT status, time FROM friends_list WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
                (user1, user2, user1, user2),
            )

            if old_request:
                if old_request[0] == "accepted":
                    await shared.bot.send_message(
                        message.chat.id,
                        f"Вы уже друзья с @{username}. Попробуйте другой юзернейм",
                    )
                    log_user_action(
                        message.from_user.id,
                        message.from_user.username,
                        "invalid_input",
                        f"tried to add existing friend: @{username}",
                    )
                    return

                if old_request[0] in ("waiting", "rejected"):
                    old_time = old_request[1]
                    time_since_request = (
                        datetime.now() - old_time).total_seconds() // 60

                    if time_since_request < 5:
                        await shared.bot.send_message(
                            message.chat.id,
                            f"Предыдущий запрос @{username} был отправлен менее 5 минут  назад. Попробуйте позже.",
                        )
                        log_user_action(
                            message.from_user.id,
                            message.from_user.username,
                            "invalid_input",
                            f"tried to send friend request too soon to: @{username}",
                        )
                        return
                    else:
                        await db.execute(
                            "DELETE FROM friends_list WHERE user_1 IN (%s, %s) AND user_2 IN (%s, %s)",
                            (user1, user2, user1, user2),
                        )
                        main_logger.info(
                            f"Deleted old friend request between {user1} and {user2}"
                        )

            # Создаем новый запрос дружбы
            await db.execute(
                "INSERT INTO friends_list VALUES(%s, %s, 'waiting', %s)",
                (user1, user2, datetime.now()),
            )

            await shared.bot.send_message(
                message.chat.id, f"Запрос дружбы отправлен @{username}"
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(message.chat.id)

            # Отправляем уведомление пользователю
            builder = accept_request_kb(user1)

            await shared.bot.send_message(
                friend_id,
                f"@{message.from_user.username} хочет добавить вас в друзья. Принять заявку?",
                reply_markup=builder.as_markup(),
            )

            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "send_request" f"sent friend request to: @{username}",
            )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(message.from_user.id,
                      f"Error in adding_friend: {e}", error_traceback)
            await shared.bot.send_message(
                message.chat.id, "Произошла ошибка при добавлении друга. Попробуйте позже."
            )

            await state.set_state(States.already_started)
            await set_default_keyboard(message.chat.id)
