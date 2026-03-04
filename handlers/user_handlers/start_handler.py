import traceback

from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message

from database import db
from keyboards.reply import set_default_keyboard
from log_setup import log_error, log_user_action
from shared import shared
from states import States


def setup(router):
    @router.message(
        StateFilter(default_state, States.already_started), Command(commands=["start"])
    )
    async def start_handler(message: Message, state: FSMContext):
        try:
            if not message.from_user.username:
                await shared.bot.send_message(
                    message.chat.id,
                    "Для использования этого бота вам необходимо иметь юзернейм для Телеграма!\nНастроить его можно в настройках профиля",
                )
                log_user_action(
                    message.from_user.id,
                    "no_username",
                    "start_attempt",
                    "User without username attempted to start bot",
                )
                return

            await state.set_state(States.already_started)

            # Ищем пользователя в базе
            user_exists = await db.fetch_one(
                "SELECT id, username FROM users WHERE id = %s", (message.from_user.id,)
            )

            if not user_exists:
                await db.execute(
                    "INSERT INTO users (id, username) VALUES (%s, %s)",
                    (message.from_user.id, message.from_user.username),
                )

                await shared.bot.send_message(
                    message.from_user.id,
                    f"Привет, {message.from_user.username}! Ваш профиль и вишлист созданы.",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "new_user_registration",
                    "New user registered",
                )
            else:
                # Если юзернейм поменялся — обновляем
                if user_exists[1] != message.from_user.username:
                    await db.execute(
                        "UPDATE users SET username = %s WHERE id = %s",
                        (message.from_user.username, message.from_user.id),
                    )
                await shared.bot.send_message(
                    message.from_user.id,
                    f"Привет, {message.from_user.username}! Что хочешь сделать?",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "returning_user_login",
                    "Existing user started bot",
                )

            await set_default_keyboard(message.from_user.id)

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                message.from_user.id, f"Error in start_handler: {e}", error_traceback
            )
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.",
            )
