from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def accept_request_kb(user1):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Принять",
            callback_data=f"accept_friend^{user1}",
        )
    )
    builder.add(
        types.InlineKeyboardButton(
            text="Отклонить",
            callback_data=f"reject_friend^{user1}",
        )
    )
    return builder
