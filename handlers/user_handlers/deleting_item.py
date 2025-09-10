from states import States
from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.filters.state import StateFilter
from database import db
from shared import shared
from log_setup import log_user_action, log_error
import traceback


def setup(router):
    @router.callback_query(F.data.startswith("del_"), StateFilter(States.deleting_item))
    async def delete_item(callback_query: CallbackQuery):
        try:
            # Получаем индекс товара из callback_data
            item_index = int(callback_query.data.replace("del_", ""))

            # Получаем данные пользователя
            username = callback_query.from_user.username
            list_id = (
                await db.fetch_one(
                    "SELECT list_id FROM users WHERE id = %s",
                    (callback_query.from_user.id,),
                )
            )[0]
            wishes = [
                i for i in await db.fetch_all(f"SELECT stuff_link, id FROM {list_id}")
            ]

            # Удаляем товар по индексу
            if item_index in [i[1] for i in wishes]:
                deleted_item = list(filter(lambda x: x[1] == item_index, wishes))[0][0]
                await db.execute(
                    f"DELETE FROM {list_id} WHERE stuff_link = %s", (deleted_item,)
                )
                await db.execute(
                    "DELETE FROM want_to_present WHERE host_list = %s AND gift = %s",
                    (username, item_index),
                )

                await callback_query.answer("Товар удален")
                await callback_query.message.delete()
                log_user_action(
                    callback_query.from_user.id,
                    username,
                    "delete_item_success",
                    f"Deleted item: {deleted_item}",
                )
            else:
                await callback_query.answer("Товар не найден")
                log_user_action(
                    callback_query.from_user.id,
                    username,
                    "delete_item_not_found",
                    f"Item index out of range: {item_index}",
                )

        except Exception as e:
            error_traceback = traceback.format_exc()
            log_error(
                callback_query.from_user.id,
                f"Error while deleting item: {e}",
                error_traceback,
            )
            await callback_query.answer("Произошла ошибка при удалении")
            await shared.bot.send_message(
                callback_query.from_user.id,
                "Не удалось удалить товар. Пожалуйста, попробуйте позже.",
            )
