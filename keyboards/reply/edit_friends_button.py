from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
from shared import shared


async def set_edit_friends_button(chat_id: int):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="/редактировать"))
    builder.add(types.KeyboardButton(text="/вернуться"))
    await shared.bot.send_message(chat_id=chat_id, text="Для изменения списка нажмите:", reply_markup=builder.as_markup(resize_keyboard=True))
