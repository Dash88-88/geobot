from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from config import BOT_ADMINS


class AdminFilter(BoundFilter):
    async def check(self, update: types.Message or types.CallbackQuery):
        return update.from_user.id in BOT_ADMINS
