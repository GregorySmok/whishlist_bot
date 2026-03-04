import traceback

from aiogram import F
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db
from keyboards.inline import delete_item_button, stop_deleting_button
from keyboards.reply import set_default_keyboard
from log_setup import log_error, log_user_action
from shared import shared
from states import States


def setup(router):
    @router.message(StateFilter(States.already_started), F.text == "Удалить")
    async def deleting_item_handler(message: Message, state: FSMContext):
        try:
            await state.set_state(States.deleting_item)
            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "delete_item_started",
                "User initiated deleting items",
            )

            wishes = await db.fetch_all(
                "SELECT stuff_link, id FROM wishlist_items WHERE user_id = %s",
                (message.from_user.id,),
            )

            if not wishes:
                await shared.bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
                await state.set_state(States.already_started)
                await set_default_keyboard(message.from_user.id)
                return

            for item, item_id in wishes:
                builder = delete_item_button(item_id)
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
                message.from_user.id, "Произошла ошибка при загрузке списка товаров."
            )
            await state.set_state(States.already_started)
            await set_default_keyboard(message.from_user.id)
