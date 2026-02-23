from aiogram import Router

from . import (
    admin_handler,
    ban_handler,
    banlist_handler,
    close_handler,
    notification_handler,
    unban_handler,
    users_handler,
)

admin_router = Router()
admin_handler.setup(admin_router)
ban_handler.setup(admin_router)
banlist_handler.setup(admin_router)
close_handler.setup(admin_router)
notification_handler.setup(admin_router)
unban_handler.setup(admin_router)
users_handler.setup(admin_router)
__all__ = ["admin_router"]
