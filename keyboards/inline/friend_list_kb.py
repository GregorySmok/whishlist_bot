from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db
from config.config import ITEMS_PER_PAGE
from emoji import emojize


async def friends_list_kb(friends, total_friends, page):
    builder = InlineKeyboardBuilder()
    for friend in friends:
        friend_name = (
            await db.fetch_one(
                "SELECT username FROM users WHERE id = %s", (friend,)
            )
        )[0]
        builder.add(
            types.InlineKeyboardButton(
                text=friend_name, callback_data=f"friend_{friend}"
            )
        )

    # Добавляем кнопки для навигации (расположим в отдельном ряду)
    row = []
    if page > 0:
        row.append(
            types.InlineKeyboardButton(
                text=emojize(":left_arrow:"), callback_data=f"page_{page - 1}"
            )
        )
    if (page + 1) * ITEMS_PER_PAGE < total_friends:
        row.append(
            types.InlineKeyboardButton(
                text=emojize(":right_arrow:"), callback_data=f"page_{page + 1}"
            )
        )
    if row:
        builder.row(*row)
    return builder
