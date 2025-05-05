from aiogram import F
from aiogram.types import CallbackQuery


def setup(router):
    @router.callback_query(F.data.startswith("none"))
    async def none_handler(callback_query: CallbackQuery):
        await callback_query.answer()
