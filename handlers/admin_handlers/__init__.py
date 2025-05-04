from aiogram import Router
from . import admin_handler
from . import ban_handler
from . import banlist_handler
from . import close_handler
from . import notification_handler
from . import unban_handler
from . import users_handler

admin_router = Router()
admin_handler.setup(admin_router)
ban_handler.setup(admin_router)
banlist_handler.setup(admin_router)
close_handler.setup(admin_router)
notification_handler.setup(admin_router)
unban_handler.setup(admin_router)
users_handler.setup(admin_router)
__all__ = ["admin_router"]
