from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    already_started = State()
    adding_item = State()
    deleting_item = State()
    viewing_wishlists = State()
    admin = State()
