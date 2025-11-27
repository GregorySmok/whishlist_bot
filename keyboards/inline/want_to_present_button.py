from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db


async def want_to_present_button(my_list, friend_list, id_):
    builder = InlineKeyboardBuilder()
    someone_want = await db.fetch_one(
        "SELECT gifter FROM want_to_present WHERE host_list = %s AND gift = %s",
        (friend_list, id_),
    )
    if someone_want:
        someone_want = someone_want[0]
        if someone_want == my_list:
            builder.add(
                types.InlineKeyboardButton(
                    text="Вы уже дарите это",
                    callback_data=f"want^{friend_list}^{id_}^del",
                )
            )
        elif someone_want != my_list:
            builder.add(
                types.InlineKeyboardButton(
                    text=f"Это уже кто-то дарит", callback_data="none"
                )
            )
    else:
        builder.add(
            types.InlineKeyboardButton(
                text="Хочу подарить", callback_data=f"want^{friend_list}^{id_}^add"
            )
        )
    return builder
