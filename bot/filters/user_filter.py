from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from logics import UserLogics
from models import User


class UserFilter(BoundFilter):
    def __init__(self, only_managers: bool = False, only_valid=False, *args, **kwargs):
        self.only_managers = only_managers
        self.only_valid = only_valid

        super().__init__(*args, **kwargs)

    async def check(self, update: types.Message or types.CallbackQuery):
        user = UserLogics.get_by_chat_id(update.from_user.id)

        if not user or user.is_blocked:
            return False

        if not user.is_active:
            user.is_active = True
            user.save(only=(User.is_active,))

        if self.only_managers and not user.is_manager:
            return False

        if self.only_valid and not user.is_valid:
            return False

        return True
