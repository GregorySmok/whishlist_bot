import traceback

from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db
from keyboards.reply import set_default_keyboard
from log_setup import log_error, log_user_action
from shared import shared
from states import States
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

            if await check_link_liquidity(item_link):
                # Проверка на дубликат у этого пользователя
                exists = await db.fetch_one(
                    "SELECT id FROM wishlist_items WHERE user_id = %s AND stuff_link = %s",
                    (message.from_user.id, item_link),
                )

                if exists:
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
                    "INSERT INTO wishlist_items (user_id, stuff_link) VALUES (%s, %s)",
                    (message.from_user.id, item_link),
                )
                await shared.bot.send_message(
                    message.from_user.id, "Товар добавлен в ваш список."
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
                    "Ошибка: ссылка не найдена или недоступна. Пожалуйста, убедитесь, что ссылка начинается с 'https://'.",
                )
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "add_item_invalid_link",
                    f"User tried to add invalid link: {item_link}",
                )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                message.from_user.id, f"Error in adding_item: {e}", error_traceback
            )
            await shared.bot.send_message(
                message.from_user.id, "Произошла ошибка при добавлении товара."
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
