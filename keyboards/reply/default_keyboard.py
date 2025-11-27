from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import types
from shared import shared
from log_setup import log_error
import traceback
from emoji import emojize


async def set_default_keyboard(chat_id):
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            types.KeyboardButton(text=emojize(":memo: Мой вишлист")),
            types.KeyboardButton(text=emojize(":busts_in_silhouette: Друзья")),
        )
        builder.row(
            types.KeyboardButton(text=emojize(":wrapped_gift: Добавить")),
            types.KeyboardButton(text=emojize(":wastebasket: Удалить")),
        )
        builder.row(
            types.KeyboardButton(
                text=emojize(":magnifying_glass_tilted_left: Добавить друга"),
                request_user=types.KeyboardButtonRequestUser(
                    request_id=1, user_is_bot=False
                ),
            )
        )
        await shared.bot.send_message(
            chat_id,
            "Выберите действие:",
            reply_markup=builder.as_markup(resize_keyboard=True),
        )
    except Exception as e:
        log_error(
            chat_id, f"Error setting default keyboard: {e}", traceback.format_exc()
        )
        await shared.bot.send_message(
            chat_id,
            "Произошла ошибка при настройке клавиатуры. Пожалуйста, попробуйте позже или используйте текстовые команды.",
        )
