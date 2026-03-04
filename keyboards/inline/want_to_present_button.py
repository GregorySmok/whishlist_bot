from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db


async def want_to_present_button(my_id, friend_id, gift_id):
    builder = InlineKeyboardBuilder()

    someone_want = await db.fetch_one(
        "SELECT gifter FROM want_to_present WHERE gift = %s", (gift_id,)
    )

    if someone_want:
        gifter_id = someone_want[0]
        if gifter_id == my_id:
            builder.add(
                types.InlineKeyboardButton(
                    text="Вы уже дарите это",
                    callback_data=f"want^{friend_id}^{gift_id}^del",
                )
            )
        else:
            builder.add(
                types.InlineKeyboardButton(
                    text="Это уже кто-то дарит", callback_data="none"
                )
            )
    else:
        builder.add(
            types.InlineKeyboardButton(
                text="Хочу подарить", callback_data=f"want^{friend_id}^{gift_id}^add"
            )
        )

    return builder
