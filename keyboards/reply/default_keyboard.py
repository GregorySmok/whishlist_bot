import traceback

from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from log_setup import log_error
from shared import shared


async def set_default_keyboard(chat_id):
    try:
        builder = ReplyKeyboardBuilder()

        # Вместо обычных эмодзи в тексте, используем чистый текст и параметр icon_custom_emoji_id
        builder.row(
            types.KeyboardButton(
                text="Мой вишлист",
                icon_custom_emoji_id="5257965174979042426",  # Замени на ID твоего красивого Premium-эмодзи
            ),
            types.KeyboardButton(
                text="Друзья", icon_custom_emoji_id="5260535596941582167"
            ),
        )
        builder.row(
            types.KeyboardButton(
                text="Добавить", icon_custom_emoji_id="5274008024585871702"
            ),
            types.KeyboardButton(
                text="Удалить", icon_custom_emoji_id="5258130763148172425"
            ),
        )
        builder.row(
            types.KeyboardButton(
                text="Добавить друга",
                icon_custom_emoji_id="5258362837411045098",
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
            "Произошла ошибка при настройке клавиатуры. Пожалуйста, попробуйте позже.",
        )
