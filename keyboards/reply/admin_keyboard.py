from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from shared import shared


async def set_admin_keyboard(chat_id):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="/users"), types.KeyboardButton(text="/banlist")
    )
    builder.row(
        types.KeyboardButton(text="/close"),
    )
    await shared.bot.send_message(
        chat_id,
        "Admin panel activated",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
