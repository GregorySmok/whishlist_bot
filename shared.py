from aiogram import Bot, Dispatcher


class Shared:
    def __init__(self):
        self.bot: Bot = None
        self.dp: Dispatcher = None


shared = Shared()
