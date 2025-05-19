from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from keyboards.reply import set_default_keyboard


def setup(router):
    @router.message(StateFilter(States.already_started), Command(commands=["вернуться"]))
    async def back_handler(message: Message):
        await set_default_keyboard(message.from_user.id)
