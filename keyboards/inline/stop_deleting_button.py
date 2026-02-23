from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder


def stop_deleting_button():
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Закончить", callback_data="stop_deleting")
    )
    return builder
