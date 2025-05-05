from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db


async def want_to_present_button(callback_query, friend_name, id_):
    builder = InlineKeyboardBuilder()
    someone_want = (await db.fetch_one("SELECT gifter FROM want_to_present WHERE host_list = %s AND gift = %s", (friend_name, id_)))
    if someone_want:
        someone_want = someone_want[0]
        if someone_want == callback_query.from_user.username:
            builder.add(
                types.InlineKeyboardButton(
                    text="Вы уже дарите это", callback_data=f"want^{friend_name}^{id_}^del"
                )
            )
        elif someone_want != callback_query.from_user.username:
            builder.add(
                types.InlineKeyboardButton(
                    text=f"Это уже дарит @{someone_want}", callback_data="none"
                )
            )
    else:
        builder.add(
            types.InlineKeyboardButton(
                text="Хочу подарить", callback_data=f"want^{friend_name}^{id_}^add"
            )
        )
    return builder
