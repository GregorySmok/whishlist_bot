from keyboards.reply import set_admin_keyboard
from states import States
from aiogram.types import Message
from config import config
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext


def setup(router):
    @router.message(StateFilter(States.already_started), Command(commands=["admin"]))
    async def admin_handler(message: Message, state: FSMContext):
        if message.chat.id in config.admins:
            await state.set_state(States.admin)
            await set_admin_keyboard(message.chat.id)
