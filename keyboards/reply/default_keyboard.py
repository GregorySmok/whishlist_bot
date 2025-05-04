from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
from shared import shared
from log_setup import log_error
import traceback


async def set_default_keyboard(chat_id):
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            types.KeyboardButton(text="/мой_вишлист"),
            types.KeyboardButton(text="/друзья"),
        )
        builder.row(
            types.KeyboardButton(text="/добавить"),
            types.KeyboardButton(text="/удалить"),
        )
        builder.row(types.KeyboardButton(
            text="/добавить_друга", request_user=types.KeyboardButtonRequestUser(request_id=1, user_is_bot=False)))
        await shared.bot.send_message(
            chat_id,
            "Выберите действие:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
    except Exception as e:
        log_error(
            chat_id, f"Error setting default keyboard: {e}", traceback.format_exc(
            )
        )
        await shared.bot.send_message(
            chat_id,
            "Произошла ошибка при настройке клавиатуры. Пожалуйста, попробуйте позже или используйте текстовые команды.",
        )
