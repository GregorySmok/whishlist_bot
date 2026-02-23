from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db


async def update_present_button(callback_query, action, friend_list, gift_id):
    skip = False
    new_markup = InlineKeyboardBuilder()
    someone_want = await db.fetch_one(
        "SELECT gifter FROM want_to_present WHERE host_list = %s AND gift = %s",
        (friend_list, gift_id),
    )
    my_list = (
        await db.fetch_one(
            "SELECT list_id FROM users WHERE id = %s", (callback_query.from_user.id)
        )
    )[0]
    if someone_want:
        someone_want = someone_want[0]
        if someone_want != my_list:
            new_markup.add(
                types.InlineKeyboardButton(
                    text="Это уже кто-то дарит", callback_data="none"
                )
            )
            skip = True
    if not skip:
        if action == "del":
            await db.execute(
                "DELETE FROM want_to_present WHERE host_list = %s AND gift = %s AND gifter = %s",
                (friend_list, gift_id, my_list),
            )
            new_markup.add(
                types.InlineKeyboardButton(
                    text="Хочу подарить",
                    callback_data=f"want^{friend_list}^{gift_id}^add",
                )
            )
        elif action == "add":
            await db.execute(
                "INSERT INTO want_to_present (host_list, gift, gifter) VALUES (%s, %s, %s)",
                (friend_list, gift_id, my_list),
            )
            new_markup.add(
                types.InlineKeyboardButton(
                    text="Вы уже дарите это",
                    callback_data=f"want^{friend_list}^{gift_id}^del",
                )
            )
    return new_markup
