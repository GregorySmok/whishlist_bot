from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from emoji import emojize

from config.config import ITEMS_PER_PAGE
from database import db


async def friends_list_kb(friends, total_friends, page):
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки друзей
    for friend in friends:
        friend_name = (
            await db.fetch_one("SELECT username FROM users WHERE id = %s", (friend,))
        )[0]
        builder.add(
            types.InlineKeyboardButton(
                text=friend_name, callback_data=f"friend_{friend}"
            )
        )

    # Создаем ряд для навигационных кнопок
    navigation_buttons = []

    # Кнопка "Назад"
    if page > 0:
        navigation_buttons.append(
            types.InlineKeyboardButton(
                text=emojize(":left_arrow:"), callback_data=f"page_{page - 1}"
            )
        )

    # Кнопка "Вперед"
    if (page + 1) * ITEMS_PER_PAGE < total_friends:
        navigation_buttons.append(
            types.InlineKeyboardButton(
                text=emojize(":right_arrow:"), callback_data=f"page_{page + 1}"
            )
        )

    # Добавляем навигационные кнопки в отдельный ряд
    if navigation_buttons:
        builder.row(*navigation_buttons)
    return builder
