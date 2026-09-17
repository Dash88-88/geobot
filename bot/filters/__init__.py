from aiogram import Dispatcher
# from .admin_filter import AdminFilter
from .user_filter import UserFilter


def setup(dp: Dispatcher):
    # dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(UserFilter)
