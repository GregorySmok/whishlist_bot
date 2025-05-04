from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from log_setup import log_user_action, log_error
import traceback
from keyboards.reply import set_default_keyboard


def setup(router):
    @router.message(
        StateFilter(default_state, States.already_started), Command(
            commands=["start"])
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
            users_list = [i[0] for i in await db.fetch_all("SELECT id FROM users")]

            if message.from_user.id not in users_list:
                await db.execute(
                    "INSERT INTO users (id, username) VALUES (%s, %s)",
                    (message.from_user.id, message.from_user.username),
                )
                await db.execute(
                    f"CREATE TABLE {message.from_user.username} (id INT AUTO_INCREMENT PRIMARY KEY, stuff_link VARCHAR(2048))"
                )

                await shared.bot.send_message(
                    message.from_user.id,
                    f"Привет, {message.from_user.username}! Ваш вишлист создан.",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "new_user_registration",
                    "New user registered",
                )
            else:
                await shared.bot.send_message(
                    message.from_user.id,
                    f"Привет, {message.from_user.username}! Что хочешь сделать ?",
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
            log_error(message.from_user.id,
                      f"Error in start_handler: {e}", error_traceback)
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже или обратитесь к администратору.",
            )
