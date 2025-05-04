from . import start_handler
from aiogram import Router

user_router = Router()
start_handler.setup(user_router)
__all__ = ["user_router"]
