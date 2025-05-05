from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db


async def update_present_button(callback_query, action, friend_name, gift_id):
    skip = False
    new_markup = InlineKeyboardBuilder()
    someone_want = (await db.fetch_one("SELECT gifter FROM want_to_present WHERE host_list = %s AND gift = %s", (friend_name, gift_id)))
    if someone_want:
        someone_want = someone_want[0]
        if someone_want != callback_query.from_user.username:
            new_markup.add(
                types.InlineKeyboardButton(
                    text=f"Это уже дарит @{someone_want}", callback_data="none"
                )
            )
            skip = True
    if not skip:
        if action == "del":
            await db.execute(
                "DELETE FROM want_to_present WHERE host_list = %s AND gift = %s AND gifter = %s",
                (friend_name, gift_id, callback_query.from_user.username),
            )
            new_markup.add(types.InlineKeyboardButton(
                text="Хочу подарить", callback_data=f"want^{friend_name}^{gift_id}^add"))
        elif action == "add":
            await db.execute(
                "INSERT INTO want_to_present (host_list, gift, gifter) VALUES (%s, %s, %s)",
                (friend_name, gift_id, callback_query.from_user.username),
            )
            new_markup.add(types.InlineKeyboardButton(
                text="Вы уже дарите это", callback_data=f"want^{friend_name}^{gift_id}^del"))
    return new_markup
