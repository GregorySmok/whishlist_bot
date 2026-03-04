from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db


async def update_present_button(callback_query, action, friend_id, gift_id):
    skip = False
    new_markup = InlineKeyboardBuilder()

    someone_want = await db.fetch_one(
        "SELECT gifter FROM want_to_present WHERE gift = %s", (gift_id,)
    )
    my_id = callback_query.from_user.id

    if someone_want:
        gifter_id = someone_want[0]
        if gifter_id != my_id:
            new_markup.add(
                types.InlineKeyboardButton(
                    text="Это уже кто-то дарит", callback_data="none"
                )
            )
            skip = True

    if not skip:
        if action == "del":
            await db.execute(
                "DELETE FROM want_to_present WHERE gift = %s AND gifter = %s",
                (gift_id, my_id),
            )
            new_markup.add(
                types.InlineKeyboardButton(
                    text="Хочу подарить",
                    callback_data=f"want^{friend_id}^{gift_id}^add",
                )
            )
        elif action == "add":
            await db.execute(
                "INSERT INTO want_to_present (host_id, gift, gifter) VALUES (%s, %s, %s)",
                (friend_id, gift_id, my_id),
            )
            new_markup.add(
                types.InlineKeyboardButton(
                    text="Вы уже дарите это",
                    callback_data=f"want^{friend_id}^{gift_id}^del",
                )
            )

    return new_markup
