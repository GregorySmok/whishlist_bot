import traceback

from aiogram import F, types
from aiogram.filters.state import StateFilter
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from emoji import emojize

from database import db
from keyboards.reply import set_default_keyboard
from log_setup import log_error, log_user_action
from shared import shared
from states import States


def setup(router):
    @router.message(
        StateFilter(States.already_started), F.text == emojize(":memo: Мой вишлист")
    )
    async def my_wishlist_handler(message: Message):
        try:
            list_id = (
                await db.fetch_one(
                    "SELECT list_id FROM users WHERE id = %s", (message.from_user.id,)
                )
            )[0]
            wishlist = [
                i for i in await db.fetch_all(f"SELECT id, stuff_link FROM {list_id}")
            ]

            if not wishlist:
                await shared.bot.send_message(message.from_user.id, "Ваш вишлист пуст.")
                await set_default_keyboard(message.from_user.id)
                log_user_action(
                    message.from_user.id,
                    message.from_user.username,
                    "view_empty_wishlist",
                    "User viewed empty wishlist",
                )
                return

            await shared.bot.send_message(message.from_user.id, "Ваш вишлист:")
            for id_, link in wishlist:
                booked = await db.fetch_one(
                    "SELECT gifter FROM want_to_present WHERE gift = %s AND host_list = %s",
                    (id_, list_id),
                )

                builder = InlineKeyboardBuilder()
                if booked:
                    builder.add(
                        types.InlineKeyboardButton(
                            text="Забронировано", callback_data="none"
                        )
                    )
                    await shared.bot.send_message(
                        message.from_user.id, link, reply_markup=builder.as_markup()
                    )
                else:
                    await shared.bot.send_message(message.from_user.id, link)

            log_user_action(
                message.from_user.id,
                message.from_user.username,
                "view_wishlist",
                f"User viewed wishlist with {len(wishlist)} items",
            )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                message.from_user.id,
                f"Error in my_wishlist_handler: {e}",
                error_traceback,
            )
            await shared.bot.send_message(
                message.from_user.id,
                "Произошла ошибка при загрузке вишлиста. Пожалуйста, попробуйте позже.",
            )
            await set_default_keyboard(message.from_user.id)
