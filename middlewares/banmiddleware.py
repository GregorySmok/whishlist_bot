from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import Message

from database import db


class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, находится ли пользователь в бан-листе
        user_id = event.from_user.id

        # Здесь выполняем запрос к базе данных для проверки
        is_banned = await self.is_user_banned(user_id)

        if is_banned:
            # Если пользователь в бан-листе, прерываем обработку
            # Можно также отправить сообщение о том, что пользователь заблокирован
            await event.answer("Вы заблокированы")
            raise CancelHandler()

        # Если пользователь не в бан-листе, продолжаем обработку
        return await handler(event, data)

    async def is_user_banned(self, user_id: int) -> bool:
        result = await db.fetch_one(
            "SELECT user_id FROM banlist WHERE user_id = %s", (user_id,)
        )
        return bool(result)
