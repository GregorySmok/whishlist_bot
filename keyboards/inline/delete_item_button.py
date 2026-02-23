from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def delete_item_button(index):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Удалить", callback_data=f"del_{index}")
    )
    return builder
