from aiogram.types import Message
from database import db
from log_setup import log_user_action, log_error
import traceback
from config.config import ITEMS_PER_PAGE
from keyboards.inline import friends_list_kb


async def show_friends_page(message: Message, user_id: int, page: int):
    try:
        friends = [
            i[0] if i[1] == user_id else i[1]
            for i in await db.fetch_all(
                "SELECT user_1, user_2 FROM friends_list WHERE (user_1 = %s OR user_2 = %s) AND status = 'accepted' LIMIT %s OFFSET %s",
                (user_id, user_id, ITEMS_PER_PAGE, page * ITEMS_PER_PAGE),
            )
        ]

        # Получаем общее количество друзей
        total_friends = (
            await db.fetch_one(
                "SELECT COUNT(*) FROM friends_list WHERE (user_1 = %s OR user_2 = %s) AND status = 'accepted'",
                (user_id, user_id),
            )
        )[0]

        if not friends:
            if page == 0:
                await message.answer(
                    "У вас пока нет друзей. Добавьте друга, используя команду /добавить_друга"
                )
                log_user_action(
                    user_id,
                    (
                        await db.fetch_one(
                            "SELECT username FROM users WHERE id = %s", (
                                user_id,)
                        )
                    )[0],
                    "view_empty_friends_list",
                    "User viewed empty friends list",
                )
                return
            else:
                # Если на этой странице нет друзей, но они есть на предыдущих страницах
                await message.answer("На этой странице больше нет друзей.")
                return

        # Создаем клавиатуру с кнопками для друзей
        builder = await friends_list_kb(friends, total_friends, page)

        # Редактируем сообщение, если оно уже существует
        if hasattr(message, "message_id") and message.message_id:
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    text=f"Страница {page + 1}. Выберите друга:",
                    reply_markup=builder.as_markup(),
                )
            except Exception as e:
                await message.answer(
                    f"Страница {page + 1}. Выберите друга:",
                    reply_markup=builder.as_markup(),
                )
        else:
            # Если сообщение новое (например, первая страница)
            await message.answer(
                f"Страница {page + 1}. Выберите друга:",
                reply_markup=builder.as_markup(),
            )
        log_user_action(
            user_id,
            (
                await db.fetch_one(
                    "SELECT username FROM users WHERE id = %s", (user_id,)
                )
            )[0],
            "view_friends_page",
            f"User viewed friends page {page + 1} with {len(friends)} friends",
        )

    except Exception as e:
        error_traceback = traceback.format_exc()
        log_error(user_id, f"Error in show_friends_page: {e}", error_traceback)
        await message.answer(
            "Произошла ошибка при загрузке списка друзей. Пожалуйста, попробуйте позже."
        )
