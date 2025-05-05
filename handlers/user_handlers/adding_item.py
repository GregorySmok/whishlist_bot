from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from database import db
from shared import shared
from aiogram.fsm.context import FSMContext
from log_setup import log_user_action, log_error
import traceback
from keyboards.reply import set_default_keyboard
from utils import check_link_liquidity


def setup(router):
    @router.message(StateFilter(States.adding_item))
    async def adding_item(message: Message, state: FSMContext):
        try:
            item_link = message.text

            if item_link == "0":
                await state.set_state(States.already_started)
                await set_default_keyboard(message.from_user.id)
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "add_item_cancelled",
                    "User cancelled adding item",
                )
                return

            goods = [
                i[0]
                for i in await db.fetch_all(
                    f"SELECT stuff_link FROM {message.from_user.username}"
                )
            ]

            if await check_link_liquidity(item_link):
                if item_link in goods:
                    await shared.bot.send_message(
                        message.from_user.id,
                        "Ошибка: ссылка уже есть в вашем списке. Попробуйте другую",
                    )
                    log_user_action(
                        message.from_user.id,
                        message.from_user.username,
                        "add_item_duplicate",
                        f"User tried to add duplicate link: {item_link}",
                    )
                    return

                await db.execute(
                    f"INSERT INTO {message.from_user.username} (stuff_link) VALUES (%s)",
                    (item_link,),
                )
                await shared.bot.send_message(
                    message.from_user.id, f"Товар добавлен в ваш список."
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "add_item_success",
                    f"Added item: {item_link}",
                )

                await state.set_state(States.already_started)
                await set_default_keyboard(message.from_user.id)
            else:
                await shared.bot.send_message(
                    message.from_user.id,
                    "Ошибка: ссылка не найдена или недоступна. Пожалуйста, убедитесь, что ссылка начинается с 'https://' и попробуйте снова.",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "add_item_invalid_link",
                    f"User tried to add invalid link: {item_link}",
                )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(message.from_user.id,
                      f"Error in adding_item: {e}", error_traceback)
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при добавлении товара. Пожалуйста, проверьте формат ссылки и попробуйте снова.",
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
