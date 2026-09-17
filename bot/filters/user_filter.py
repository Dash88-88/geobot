from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from config import BOT_ADMINS
from logics import UserLogics
from models import User


class UserFilter(BoundFilter):
    def __init__(self, only_managers: bool = False, only_valid=False, *args, **kwargs):
        self.only_managers = only_managers
        self.only_valid = only_valid

        super().__init__(*args, **kwargs)

    async def check(self, update: types.Message or types.CallbackQuery):
        user_id = update.from_user.id
        user = UserLogics.get_by_chat_id(user_id)

        if not user:
            if user_id in BOT_ADMINS:
                user = UserLogics.create(
                    chat_id=user_id,
                    username=update.from_user.username,
                    nickname=update.from_user.username or update.from_user.first_name or str(user_id),
                    site_id='',
                    is_manager=True
                )
            else:
                return False

        if user.is_blocked:
            return False

        if not user.is_active:
            user.is_active = True
            user.save(only=(User.is_active,))

        if user_id in BOT_ADMINS and not user.is_manager:
            user.is_manager = True
            user.save(only=(User.is_manager,))

        if self.only_managers and not (user.is_manager or user_id in BOT_ADMINS):
            return False

        if self.only_valid and not user.is_valid:
            return False

        return True
