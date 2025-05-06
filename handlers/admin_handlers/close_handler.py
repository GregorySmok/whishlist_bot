from states import States
from aiogram.types import Message
from aiogram.filters.state import StateFilter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.reply import set_default_keyboard
from log_setup import log_admin_action


def setup(router):
    @router.message(StateFilter(States.admin), Command(commands=["close"]))
    async def close_handler(message: Message, state: FSMContext):
        await state.set_state(States.already_started)
        await set_default_keyboard(message.chat.id)
        
        # Логирование действия администратора
        log_admin_action(
            admin_id=message.chat.id,
            admin_username=message.from_user.username or str(message.chat.id),
            action="admin_panel_close",
            details="Выход из панели администратора"
        )