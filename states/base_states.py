from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    already_started = State()
    adding_item = State()
    deleting_item = State()
    viewing_wishlists = State()
    admin = State()
