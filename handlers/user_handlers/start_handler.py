import traceback
from random import choices

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
            users_list = [i[0] for i in await db.fetch_all("SELECT id FROM users")]

            if message.from_user.id not in users_list:
                is_id = False
                existing_ids = await db.fetch_all("SELECT list_id FROM users")
                existing_ids = (
                    [id_[0] for id_ in existing_ids] if existing_ids else None
                )

                while not is_id:
                    id_ = "".join(choices("0123456789qwertyuiopasdfghjklzxcvbnm", k=6))
                    if id_ not in existing_ids:
                        is_id = True
                await db.execute(
                    "INSERT INTO users (id, username, list_id) VALUES (%s, %s, %s)",
                    (message.from_user.id, message.from_user.username, id_),
                )
                await db.execute(
                    f"CREATE TABLE {id_} (id INT AUTO_INCREMENT PRIMARY KEY, stuff_link VARCHAR(2048))"
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
                list_id = (
                    await db.fetch_one(
                        "SELECT list_id FROM users WHERE id = %s",
                        (message.from_user.id,),
                    )
                )[0]
                if not list_id:
                    username = (
                        await db.fetch_one(
                            "SELECT username FROM users WHERE id = %s",
                            (message.from_user.id,),
                        )
                    )[0]
                    is_id = False
                    existing_ids = await db.fetch_all("SELECT list_id FROM users")
                    existing_ids = (
                        [id_[0] for id_ in existing_ids] if existing_ids else None
                    )

                    while not is_id:
                        id_ = "".join(
                            choices("0123456789qwertyuiopasdfghjklzxcvbnm", k=6)
                        )
                        if id_ not in existing_ids:
                            is_id = True
                    await db.execute(
                        "UPDATE users SET list_id = %s, username = %s WHERE id = %s",
                        (id_, message.from_user.username, message.from_user.id),
                    )
                    await db.execute(f"RENAME TABLE {username} TO {id_}")
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
            log_error(
                message.from_user.id, f"Error in start_handler: {e}", error_traceback
            )
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже или обратитесь к администратору.",
            )
