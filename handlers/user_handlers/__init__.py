from matplotlib import use
from . import delete_item_handler
from . import deleting_item
from . import start_handler
from . import add_item_handler
from . import adding_item
from . import stop_deleting_item
from . import my_wishlist_handler
from . import friend_handler
from . import friend_selection_handler
from . import want_to_gift_handler
from . import none_handler
from . import page_selection_handler
from . import adding_friend_handler
from . import accept_request_handler
from . import reject_request_handler
from . import refresh_handler
from aiogram import Router

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
