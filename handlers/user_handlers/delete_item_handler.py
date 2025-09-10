from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from database import db
from shared import shared
from aiogram.fsm.context import FSMContext
from log_setup import log_user_action, log_error
import traceback
from keyboards.reply import set_default_keyboard
from keyboards.inline import delete_item_button, stop_deleting_button


def setup(router):
    @router.message(StateFilter(States.already_started), Command(commands=["удалить"]))
    async def deleting_item_handler(message: Message, state: FSMContext):
        try:
            await state.set_state(States.deleting_item)
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "delete_item_started",
                "User initiated deleting items",
            )
            list_id = (
                await db.fetch_one(
                    "SELECT list_id FROM users WHERE id = %s",
                    (message.from_user.id,),
                )
            )[0]
            wishes = [
                i for i in await db.fetch_all(f"SELECT stuff_link, id FROM {list_id}")
            ]

            if not wishes:
                await shared.bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
                await state.set_state(States.already_started)
                await set_default_keyboard(message.from_user.id)
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "delete_item_empty_list",
                    "User tried to delete from empty wishlist",
                )
                return

            # Отправляем каждый товар с кнопкой удаления
            for item, index in wishes:
                builder = delete_item_button(index)
                await shared.bot.send_message(
                    message.from_user.id, item, reply_markup=builder.as_markup()
                )

            builder = stop_deleting_button()
            await shared.bot.send_message(
                message.from_user.id,
                "Для завершения нажмите:",
                reply_markup=builder.as_markup(),
            )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                message.from_user.id,
                f"Error in deleting_item_handler: {e}",
                error_traceback,
            )
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при загрузке списка товаров. Пожалуйста, попробуйте позже.",
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
