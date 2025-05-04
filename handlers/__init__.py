from .admin_handlers import admin_router
from .user_handlers import user_router


routers = [admin_router, user_router]
__all__ = ['routers']
