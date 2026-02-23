from aiogram import Router

from . import (
    accept_request_handler,
    add_item_handler,
    adding_friend_handler,
    adding_item,
    delete_item_handler,
    deleting_item,
    friend_handler,
    friend_selection_handler,
    my_wishlist_handler,
    none_handler,
    page_selection_handler,
    refresh_handler,
    reject_request_handler,
    start_handler,
    stop_deleting_item,
    want_to_gift_handler,
)

user_router = Router()
start_handler.setup(user_router)
add_item_handler.setup(user_router)
adding_item.setup(user_router)
deleting_item.setup(user_router)
stop_deleting_item.setup(user_router)
delete_item_handler.setup(user_router)
my_wishlist_handler.setup(user_router)
friend_handler.setup(user_router)
friend_selection_handler.setup(user_router)
want_to_gift_handler.setup(user_router)
none_handler.setup(user_router)
page_selection_handler.setup(user_router)
adding_friend_handler.setup(user_router)
accept_request_handler.setup(user_router)
reject_request_handler.setup(user_router)
refresh_handler.setup(user_router)
__all__ = ["user_router"]
